import csv
import io
import os
from datetime import date
from urllib.parse import urlencode

from flask import Flask, Response, abort, g, render_template, request, send_from_directory
from markupsafe import Markup, escape

from . import extract, gbif, groups, i18n, photos, queries, taicol
from .db import close_db, get_db

MAJOR_RANKS = ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species']
INFRA_RANKS = {'Subspecies', 'Variety', 'Form', 'Subvariety', 'Subform', 'Special Form', 'Race', 'Stirps', 'Morph', 'Aberration', 'Hybrid Formula'}
TREE_LIMIT = 200
COMPARE_MAX = 4
LAYOUTS = ('guide', 'sheet', 'article')  # species page; field guide is the default
# facts shown under the field guide's biology tab rather than the overview
DIST_FACTS = {'fact_in_taiwan', 'fact_endemic', 'fact_alien', 'fact_alien_note', 'fact_habitat', 'fact_fossil'}
VENDOR = os.environ.get('SPECIES123_VENDOR', '/code/vendor')  # musubii.css, copied in the Docker build
# external links in display order. Ids come from Wikidata (matched on the TaiCOL id) or, for GBIF and
# iNaturalist only, from an exact accepted-name match; gbif_legacy only when there is no post-2026 GBIF id
EXT_LINKS = [
    ('gbif', 'GBIF', 'https://www.gbif.org/taxon/{}'),
    ('gbif_legacy', 'GBIF', 'https://www.gbif.org/species/{}'),
    ('inaturalist', 'iNaturalist', 'https://www.inaturalist.org/taxa/{}'),
    ('ebird', 'eBird', 'https://ebird.org/species/{}'),
    ('xenocanto', 'xeno-canto', 'https://xeno-canto.org/species/{}'),
    ('wikidata', 'Wikidata', 'https://www.wikidata.org/wiki/{}'),
]


def italic(html):
    """TaiCOL formatted names carry <i> markup; keep only that, escape everything else."""
    if not html:
        return ''
    s = str(escape(html)).replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
    return Markup(s)


def split_names(s):
    return [x.strip() for x in (s or '').split(',') if x.strip()]


def create_app():
    app = Flask(__name__)
    app.teardown_appcontext(close_db)

    @app.before_request
    def pick_lang():
        lang = request.args.get('lang') or request.cookies.get('lang')
        g.lang = lang if lang in i18n.LANGS else i18n.DEFAULT_LANG
        g.t, g.code, g.rank = i18n.make_t(g.lang)

    @app.after_request
    def remember_lang(resp):
        if request.args.get('lang') in i18n.LANGS:
            resp.set_cookie('lang', request.args['lang'], max_age=365 * 24 * 3600, samesite='Lax')
        return resp

    @app.context_processor
    def helpers():
        return {
            'lang': g.lang, 't': g.t, 'code': g.code, 'rank_label': g.rank, 'tables': i18n,
            'badges': badges, 'url_with': url_with, 'group_label': lambda k: groups.label(k, g.lang), 'lang_url': url_with(lang='en' if g.lang == 'zh' else 'zh'),
            'data_meta': data_meta(),
        }

    app.add_template_filter(italic)

    def data_meta():
        if get_db() is None:
            return {}
        if 'meta' not in g:
            g.meta = queries.meta()
        return g.meta

    def url_with(**changes):
        """Current URL with some query args replaced (None removes)."""
        args = request.args.to_dict(flat=False)
        for k, v in changes.items():
            if v is None:
                args.pop(k, None)
            else:
                args[k] = v if isinstance(v, list) else [v]
        qs = urlencode([(k, x) for k, vs in args.items() for x in vs])
        return request.path + ('?' + qs if qs else '')

    def badges(t, compact=False):
        """Status badges as (label, MUSUBii modifier classes)."""
        out = []
        if t['is_endemic']:
            out.append((g.t('endemic'), 'is-plain is-primary'))
        if t['alien_type'] and t['alien_type'] != 'native':
            out.append((g.code(i18n.ALIEN, t['alien_type']), 'is-plain is-warning'))
        if t['protected']:
            out.append((g.t('fact_protected') + ' ' + t['protected'], 'is-plain is-danger'))
        if t['redlist'] and t['redlist'] not in ('NA', 'NE'):
            cls = i18n.THREAT_BADGE.get(i18n.REDLIST_TO_IUCN.get(t['redlist']), 'is-outline')
            label = g.code(i18n.REDLIST, t['redlist'])
            if not compact:
                label = f"{g.t('fact_redlist')} · {label}"
            out.append((label, cls))
        if not compact and t['iucn'] and t['iucn'] != 'NE':
            out.append((f"IUCN · {g.code(i18n.IUCN, t['iucn'])}", i18n.THREAT_BADGE.get(t['iucn'], 'is-outline')))
        return out

    @app.before_request
    def require_data():
        if request.endpoint not in ('static', 'healthz', 'vendor') and get_db() is None:
            return render_template('message.html', title=g.t('no_data'), hint=g.t('no_data_hint')), 503

    @app.route('/vendor/<path:filename>')
    def vendor(filename):
        return send_from_directory(VENDOR, filename, max_age=7 * 24 * 3600)

    @app.route('/healthz')
    def healthz():
        return {'ok': True, 'data': get_db() is not None}

    @app.route('/')
    def home():
        return render_template('home.html', kingdoms=queries.kingdoms(), recent=queries.recent(), groups=queries.group_cards(),
                               suggestions=['Begonia formosana', '水鴨腳', 'Ursus thibetanus', '蘭科', 'Lepidoptera'])

    def search_filters():
        f = {name: request.args.getlist(name) for name in [*queries.FACETS, 'group']}
        f['q'] = request.args.get('q', '').strip()
        return f

    @app.route('/search')
    def search():
        f = search_filters()
        page = max(request.args.get('page', 1, type=int), 1)
        sort = request.args.get('sort', '')
        under = queries.taxon(request.args['under']) if request.args.get('under') else None
        under_path = under['path'] if under else None
        total, results = queries.search(f, sort, page, under_path)
        pages = max((total + queries.PER_PAGE - 1) // queries.PER_PAGE, 1)
        active = [(name, v) for name in ['group', *queries.FACETS] for v in f[name]]
        return render_template('search.html', f=f, results=results, total=total, page=page, pages=pages, sort=sort,
                               facets=queries.facet_counts(f, under_path), active=active, under=under,
                               kingdom_zh={k['simple_name']: k['common_name_c'] for k in queries.kingdoms()})

    def tree_rows(nodes, depth, open_ids):
        out = []
        for n in nodes:
            is_open = n['taxon_id'] in open_ids
            out.append({'t': n, 'depth': depth, 'open': is_open})
            if is_open:
                kids = queries.children(n['taxon_id'], TREE_LIMIT)
                out.extend(tree_rows(kids, depth + 1, open_ids))
                if n['n_children'] > TREE_LIMIT:
                    out.append({'more': n['n_children'] - TREE_LIMIT, 'depth': depth + 1, 'parent': n})
        return out

    def node_stats(t):
        counts = queries.rank_counts(t['taxon_id'])
        start = MAJOR_RANKS.index(t['rank']) + 1 if t['rank'] in MAJOR_RANKS else 0
        return [(r, counts[r]) for r in MAJOR_RANKS[start:] if counts.get(r)]

    @app.route('/taxonomy')
    def taxonomy():
        node = queries.taxon(request.args.get('node', '')) or None
        if node is None:
            # default: Taiwan's largest kingdom
            ks = queries.kingdoms()
            node = queries.taxon(ks[0]['taxon_id']) if ks else None
        path = node['path'].split(',') if node else []
        rows = tree_rows(queries.roots(), 0, set(path))
        return render_template('taxonomy.html', rows=rows, node=node, lineage=queries.lineage(node) if node else [],
                               stats=node_stats(node) if node else [], kids=queries.children(node['taxon_id'], 100) if node else [])

    @app.route('/taxonomy/children/<taxon_id>')
    def taxonomy_children(taxon_id):
        parent = queries.taxon(taxon_id) or abort(404)
        depth = request.args.get('depth', 1, type=int)
        rows = tree_rows(queries.children(taxon_id, TREE_LIMIT), depth, set())
        if parent['n_children'] > TREE_LIMIT:
            rows.append({'more': parent['n_children'] - TREE_LIMIT, 'depth': depth, 'parent': parent})
        return render_template('_tree_rows.html', rows=rows, node=None)

    def facts(t):
        yn = lambda v: '' if v is None else g.t('yes' if v else 'no')
        habitat = '、'.join(g.t('h_' + h) for h in ('terrestrial', 'freshwater', 'brackish', 'marine') if t['is_' + h])
        if g.lang == 'en':
            habitat = habitat.replace('、', ', ')
        rows = [
            ('fact_rank', g.rank(t['rank'])),
            ('fact_author', t['name_author']),
            ('fact_in_taiwan', yn(t['is_in_taiwan'])),
            ('fact_endemic', g.t('endemic') if t['is_endemic'] else (g.t('not_endemic') if t['is_endemic'] is not None else '')),
            ('fact_alien', g.code(i18n.ALIEN, t['alien_type'])),
            ('fact_alien_note', '\n'.join(x.strip() for x in (t['alien_status_note'] or '').split('|') if x.strip())),
            ('fact_habitat', habitat),
            ('fact_fossil', g.t('yes') if t['is_fossil'] else ''),
            ('fact_redlist', g.code(i18n.REDLIST, t['redlist']) + (f" ({t['redlist']})" if t['redlist'] else '')),
            ('fact_iucn', g.code(i18n.IUCN, t['iucn']) + (f" ({t['iucn']})" if t['iucn'] else '')),
            ('fact_cites', t['cites']),
            ('fact_protected', g.code(i18n.PROTECTED, t['protected'])),
            ('fact_species', str(t['n_species']) if t['rank'] != 'Species' and t['n_species'] else ''),
        ]
        return [{'key': k, 'label': g.t(k), 'value': v} for k, v in rows if v]

    def ext_links(t, inat_id):
        x = {src: [(i, 'taicol_id' if src == 'wikidata' else 'wikidata') for i in ids]
             for src, ids in queries.xrefs(t['taxon_id']).items()}
        if 'gbif' in x:
            x.pop('gbif_legacy', None)
        elif 'gbif_legacy' not in x:
            key = gbif.taxon_key(t['simple_name'], t['kingdom'], t['rank'])
            if key:
                x['gbif_legacy'] = [(str(key), 'name')]
        if inat_id and 'inaturalist' not in x:
            x['inaturalist'] = [(str(inat_id), 'name')]  # the photos' name match
        return [{'label': label, 'id': i, 'url': url.format(i), 'via': via}
                for src, label, url in EXT_LINKS for i, via in x.get(src, [])]

    @app.route('/taxon/<taxon_id>')
    def taxon(taxon_id):
        t = queries.taxon(taxon_id)
        if t is None:
            return render_template('message.html', title=g.t('not_found'), hint=g.t('not_found_hint')), 404
        layout = request.args.get('layout') if request.args.get('layout') in LAYOUTS else LAYOUTS[0]
        vern = ([(t['common_name_c'], g.t('primary_name'))] if t['common_name_c'] else []) + \
               [(n, g.t('alt_name')) for n in split_names(t['alternative_name_c'])]
        lin = queries.lineage(t)
        cite = (f"{t['simple_name']} {t['name_author'] or ''}".strip() +
                f". TaiCOL 臺灣物種名錄. https://taicol.tw/zh-hant/taxon/{t['taxon_id']} (accessed {date.today().isoformat()})")
        pics = photos.taxon_photos(t['simple_name'], t['kingdom'])
        return render_template('taxon.html', tx=t, layout=layout, lineage=lin, crumbs=[x for x in lin if x['rank'] in MAJOR_RANKS],
                               facts=facts(t), dist_facts=DIST_FACTS, vern=vern, links=ext_links(t, pics.get('inat_id')),
                               refs=taicol.references(t['name_id']), pics=pics,
                               kids=queries.children(t['taxon_id'], 100) if t['n_children'] else [], cite=cite)

    def compare_groups(cmp):
        def lin_name(t, rank):
            return next((x['simple_name'] for x in lineage_of[t['taxon_id']] if x['rank'] == rank), '')
        lineage_of = {t['taxon_id']: queries.lineage(t) for t in cmp}
        groups = [
            ('g_taxonomy', [(g.t('fact_author'), lambda t: t['name_author']), (g.t('fact_rank'), lambda t: g.rank(t['rank']))] +
             [(g.rank(r), (lambda r: lambda t: lin_name(t, r))(r)) for r in ('Genus', 'Family', 'Order', 'Class', 'Phylum')]),
            ('g_names', [(g.t('primary_name'), lambda t: t['common_name_c']), (g.t('alt_name'), lambda t: t['alternative_name_c'])]),
            ('g_conservation', [(g.t('fact_redlist'), lambda t: g.code(i18n.REDLIST, t['redlist'])),
                                (g.t('fact_iucn'), lambda t: g.code(i18n.IUCN, t['iucn'])),
                                (g.t('fact_cites'), lambda t: t['cites']),
                                (g.t('fact_protected'), lambda t: g.code(i18n.PROTECTED, t['protected']))]),
            ('g_ecology', [(g.t('fact_endemic'), lambda t: g.t('endemic') if t['is_endemic'] else g.t('not_endemic')),
                           (g.t('fact_alien'), lambda t: g.code(i18n.ALIEN, t['alien_type'])),
                           (g.t('fact_habitat'), lambda t: next((f['value'] for f in facts(t) if f['key'] == 'fact_habitat'), '')),
                           (g.t('fact_in_taiwan'), lambda t: g.t('yes') if t['is_in_taiwan'] else g.t('no'))]),
        ]
        out = []
        for title, attrs in groups:
            rows = []
            for label, fn in attrs:
                cells = [fn(t) or '—' for t in cmp]
                rows.append({'label': label, 'cells': cells, 'differs': len(cmp) > 1 and len(set(cells)) > 1})
            out.append({'title': g.t(title), 'rows': rows})
        return out

    @app.route('/compare')
    def compare():
        ids = [i for i in request.args.get('ids', '').split(',') if i][:COMPARE_MAX]
        cmp = queries.taxa(list(dict.fromkeys(ids)))
        suggest = []
        for t in cmp:
            suggest += [s for s in queries.siblings(t, [c['taxon_id'] for c in cmp] + [s['taxon_id'] for s in suggest])]
        genera = {t['genus'] for t in cmp}
        return render_template('compare.html', cmp=cmp, groups=compare_groups(cmp) if cmp else [], suggest=suggest[:6],
                               ids=[t['taxon_id'] for t in cmp], same_genus=genera.pop() if len(genera) == 1 and cmp else None)

    def match_names(hits):
        """Checklist rows (one per taxon, merged across spellings) and the names that matched nothing."""
        lookup = queries.by_names({n for h in hits for n, _ in h.candidates} | {h.genus for h in hits if h.genus})
        found, missing = {}, []

        def put(taxa, verbatim, count, partial=False):
            for t in taxa:
                row = found.setdefault(t['taxon_id'], {'t': t, 'verbatim': [], 'count': 0, 'partial': False})
                if verbatim not in row['verbatim']:
                    row['verbatim'].append(verbatim)
                row['count'] += count
                row['partial'] = row['partial'] or partial

        for h in hits:
            name, verbatim = next(((n, v) for n, v in h.candidates if n in lookup), (None, None))
            if name:
                # a rank-marked infraspecific name ("… var. x") that only matched its species
                partial = name != h.candidates[0][0] and '. ' in h.candidates[0][0]
                put(lookup[name], h.candidates[0][1] if partial else verbatim, h.count, partial)
            elif h.genus in lookup:
                higher = [t for t in lookup[h.genus] if t['rank'] != 'Genus']
                put(higher or lookup[h.genus], h.genus, h.count)
                if not higher:  # "Genus epithet" with a known genus: worth reporting the epithet as missing
                    missing.append({'name': h.candidates[0][1], 'genus': lookup[h.genus][0], 'count': h.count})
        rows = sorted(found.values(), key=lambda r: (r['t']['kingdom'] or '', r['t']['family'] or '\uffff',
                                                     r['t']['depth'], r['t']['simple_name']))
        return rows, missing

    @app.route('/names', methods=['GET', 'POST'])
    def names():
        text = request.form.get('text', '')
        rows, missing = match_names(extract.names(text)) if text.strip() else ([], [])
        if request.form.get('format') == 'csv':
            out = io.StringIO()
            w = csv.writer(out)
            w.writerow(['verbatim', 'count', 'taxon_id', 'simple_name', 'name_author', 'common_name_c', 'rank',
                        'family', 'family_c', 'kingdom', 'is_endemic', 'alien_type', 'redlist', 'iucn', 'protected', 'url'])
            for r in rows:
                t = r['t']
                w.writerow(['; '.join(r['verbatim']), r['count'], t['taxon_id'], t['simple_name'], t['name_author'],
                            t['common_name_c'], t['rank'], t['family'], t['family_c'], t['kingdom'], t['is_endemic'],
                            t['alien_type'], t['redlist'], t['iucn'], t['protected'],
                            f"https://taicol.tw/zh-hant/taxon/{t['taxon_id']}"])
            for m in missing:
                w.writerow([m['name'], m['count']] + [''] * 14)
            return Response('\ufeff' + out.getvalue(), mimetype='text/csv',
                            headers={'Content-Disposition': f'attachment; filename=species123-checklist-{date.today().isoformat()}.csv'})
        n_species = sum(1 for r in rows if r['t']['rank'] == 'Species' or r['t']['rank'] in INFRA_RANKS)
        return render_template('names.html', text=text, rows=rows, missing=missing, n_species=n_species,
                               max_chars=extract.MAX_CHARS)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('message.html', title=g.t('not_found'), hint=g.t('not_found_hint')), 404

    return app
