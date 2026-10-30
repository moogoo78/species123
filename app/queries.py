"""SQL against the read-only TaiCOL snapshot."""
import hashlib

from . import groups
from .db import get_db

PER_PAGE = 50
FACETS = {
    # name: (column, multi-valued)
    'kingdom': 'kingdom',
    'rank': 'rank',
    'endemic': 'is_endemic',
    'alien': 'alien_type',
    'redlist': 'redlist',
    'protected': 'protected',
}
SORTS = {
    'name': 'simple_name',
    'common': "coalesce(common_name_c, '￿')",
    'family': "coalesce(family, '￿'), simple_name",
    'rank': 'depth, simple_name',
    'updated': 'updated_at',
}
LIST_COLS = ('taxon_id, simple_name, name_author, formatted_name, rank, common_name_c, family, family_c, kingdom, '
             'is_endemic, alien_type, iucn, redlist, protected, updated_at, n_species')


def one(sql, params=()):
    return get_db().execute(sql, params).fetchone()


def rows(sql, params=()):
    return get_db().execute(sql, params).fetchall()


def meta():
    return {r['key']: r['value'] for r in rows('SELECT key, value FROM meta')}


def taxon(taxon_id):
    return one('SELECT * FROM taxon WHERE taxon_id = ?', (taxon_id,))


def xrefs(taxon_id):
    """{source: [(id, via)]} from Wikidata (see scripts/import_taicol.py WD_PROPS); via is how the item was found:
    'taicol_id' (it carries the TaiCOL id) or 'name' (same scientific name, rank and family)."""
    out = {}
    for r in rows('SELECT source, ext_id, via FROM xref WHERE taxon_id = ? ORDER BY source, ext_id', (taxon_id,)):
        out.setdefault(r['source'], []).append((r['ext_id'], r['via']))
    return out


def wcvp(taxon_id):
    """WCVP facts for a vascular plant (scripts/import_wcvp.py), or None."""
    return one('SELECT * FROM wcvp WHERE taxon_id = ?', (taxon_id,))


def wcvp_dist(taxon_id):
    """WGSRPD level-3 regions [(area_code, name, status)], status native / introduced / extinct / doubtful."""
    return rows('SELECT d.area_code, a.name, d.status FROM wcvp_dist d JOIN wgsrpd_area a USING (area_code) '
                'WHERE d.taxon_id = ? ORDER BY a.name', (taxon_id,))


def wcvp_taiwan():
    """In-Taiwan species and below with a WCVP distribution, with WCVP's Taiwan status (wcvp_tai, None when absent)."""
    return rows(f"""SELECT {', '.join('t.' + c.strip() for c in LIST_COLS.split(','))},
                         w.name AS wcvp_name, w.authors AS wcvp_authors, d.status AS wcvp_tai
                  FROM taxon t JOIN wcvp w ON w.taxon_id = t.taxon_id
                  LEFT JOIN wcvp_dist d ON d.taxon_id = t.taxon_id AND d.area_code = 'TAI'
                  WHERE t.is_in_taiwan = 1 AND t.rank IN ('Species', 'Subspecies', 'Variety', 'Form', 'Hybrid Formula')
                    AND EXISTS (SELECT 1 FROM wcvp_dist x WHERE x.taxon_id = t.taxon_id)
                  ORDER BY t.family, t.simple_name""")


def taxa(ids):
    if not ids:
        return []
    found = {r['taxon_id']: r for r in rows(f'SELECT * FROM taxon WHERE taxon_id IN ({",".join("?" * len(ids))})', ids)}
    return [found[i] for i in ids if i in found]


def lineage(t):
    """Ancestors root → t (inclusive)."""
    ids = t['path'].split(',')
    return taxa(ids)


def children(taxon_id, limit=200):
    return rows(f'SELECT {LIST_COLS}, n_children FROM taxon WHERE parent_id = ? ORDER BY simple_name LIMIT ?', (taxon_id, limit))


# ranks a taxon may sit at the top of the tree with ('Unranked' is TaiCOL's Viruses root);
# any other parentless taxon has no classification in TaiCOL yet
TOP_RANKS = ('Superkingdom', 'Kingdom', 'Unranked')
_TOP = ', '.join(f"'{r}'" for r in TOP_RANKS)


def roots():
    return rows(f'SELECT {LIST_COLS}, n_children FROM taxon WHERE parent_id IS NULL AND rank IN ({_TOP}) AND n_children > 0 '
                'ORDER BY simple_name')


def unplaced(limit=200):
    """Parentless taxa below kingdom rank (TaiCOL gives them no parent and no kingdom), for the tree's 未歸類 node."""
    return rows(f'SELECT {LIST_COLS}, n_children FROM taxon WHERE parent_id IS NULL AND rank NOT IN ({_TOP}) '
                'ORDER BY simple_name LIMIT ?', (limit,))


def unplaced_counts():
    return one(f"SELECT count(*) AS n, sum(rank = 'Species') AS n_species FROM taxon "
               f"WHERE parent_id IS NULL AND rank NOT IN ({_TOP})")


def rank_counts(taxon_id):
    return {r['rank']: r['n'] for r in rows('SELECT rank, n FROM taxon_rank_count WHERE taxon_id = ?', (taxon_id,))}


def kingdoms():
    return rows(f"SELECT {LIST_COLS} FROM taxon WHERE rank = 'Kingdom' AND n_species > 0 ORDER BY n_species DESC")


def recent(limit=8):
    return rows(f"SELECT {LIST_COLS} FROM taxon WHERE rank = 'Species' ORDER BY updated_at DESC, simple_name LIMIT ?", (limit,))


# living, non-sensitive species in Taiwan with a Chinese name and an iNaturalist id (so most have a photo)
DAILY_POOL = ("rank = 'Species' AND is_in_taiwan = 1 AND common_name_c IS NOT NULL AND sensitive IS NULL "
              "AND coalesce(is_fossil, 0) = 0 AND coalesce(alien_type, 'native') IN ('native', 'naturalized', 'invasive') "
              "AND taxon_id IN (SELECT taxon_id FROM xref WHERE source = 'inaturalist')")


def species_of_the_day(day):
    """Same species all day for everyone: the pool row at sha256(date) mod pool size."""
    n = one(f'SELECT count(*) FROM taxon WHERE {DAILY_POOL}')[0]
    if not n:
        return None
    offset = int(hashlib.sha256(day.isoformat().encode()).hexdigest(), 16) % n
    return one(f'SELECT {LIST_COLS}, is_in_taiwan FROM taxon WHERE {DAILY_POOL} ORDER BY taxon_id LIMIT 1 OFFSET ?', (offset,))


def siblings(t, exclude, limit=6):
    """Taxa sharing t's parent (e.g. same genus), for compare suggestions."""
    if not t['parent_id']:
        return []
    marks = ','.join('?' * len(exclude))
    return rows(f'SELECT {LIST_COLS} FROM taxon WHERE parent_id = ? AND taxon_id NOT IN ({marks}) '
                'ORDER BY simple_name LIMIT ?', (t['parent_id'], *exclude, limit))


def _under_cond(root_ids):
    """SQL condition for 'under any of these taxa' (a taxon counts as under itself)."""
    roots = taxa(root_ids)
    if not roots:
        return '0', []
    params = [x for r in roots for x in (r['path'], f"{r['path']},%")]
    return '(' + ' OR '.join('path = ? OR path LIKE ?' for _ in roots) + ')', params


def _group_cond(keys):
    """SQL condition for 'under any root of these common groups'."""
    return _under_cond([r for k in keys if k in groups.BY_KEY for r in groups.BY_KEY[k][2]])


# gallery filters; the first is the default. Living species only, except under 'all'.
# TaiCOL flags some living species as fossils (they also have a fossil record); those are kept.
LIVING_DESPITE_FOSSIL_FLAG = ('t0061401', 't0064355')  # Dermochelys coriacea 革龜, Gavia stellata 紅喉潛鳥
_LIVING_TW = (f"is_in_taiwan = 1 AND (NOT coalesce(is_fossil, 0) "
              f"OR taxon_id IN ({','.join(repr(i) for i in LIVING_DESPITE_FOSSIL_FLAG)}))")
GALLERY_SHOW = {
    'taiwan': _LIVING_TW,
    'endemic': f'{_LIVING_TW} AND is_endemic = 1',
    'native': f"{_LIVING_TW} AND alien_type = 'native'",
    'alien': f"{_LIVING_TW} AND alien_type IN ('naturalized', 'invasive', 'cultured', 'cultivated')",
    'all': '1',
}


def gallery_species(root_ids, show='taiwan'):
    """Species under the roots, family by family, each with an iNaturalist id when Wikidata has one."""
    cond, params = _under_cond(root_ids)
    return rows(f"""SELECT {LIST_COLS}, is_in_taiwan,
                     (SELECT ext_id FROM xref x WHERE x.taxon_id = taxon.taxon_id AND x.source = 'inaturalist'
                      ORDER BY x.via = 'name' LIMIT 1) AS inat_id
                    FROM taxon WHERE rank = 'Species' AND {cond} AND {GALLERY_SHOW[show]}
                    ORDER BY family IS NULL, family, simple_name""", params)


def gallery_counts(root_ids):
    cond, params = _under_cond(root_ids)
    sums = ', '.join(f'sum({c})' for c in GALLERY_SHOW.values())
    return dict(zip(GALLERY_SHOW, one(f"SELECT {sums} FROM taxon WHERE rank = 'Species' AND {cond}", params)))


def group_cards():
    """Home page: each common group with its root taxa and species count."""
    out = []
    for key, zh, en, ids in groups.GROUPS:
        roots = taxa(ids)
        if roots:
            out.append({'key': key, 'zh': zh, 'en': en, 'roots': roots, 'n_species': sum(r['n_species'] for r in roots)})
    return out


def _where(f, skip=None, under_path=None):
    clauses, params = [], []
    if f.get('group') and skip != 'group':
        cond, cparams = _group_cond(f['group'])
        clauses.append(cond)
        params.extend(cparams)
    q = (f.get('q') or '').strip().lower()
    if q:
        clauses.append('search_text LIKE ?')
        params.append(f'%{q}%')
    if under_path:
        clauses.append('path LIKE ?')
        params.append(f'{under_path},%')
    for name, col in FACETS.items():
        vals = f.get(name) or []
        if name == skip or not vals:
            continue
        clauses.append(f'{col} IN ({",".join("?" * len(vals))})')
        params.extend(int(v) if name == 'endemic' else v for v in vals)
    return (' WHERE ' + ' AND '.join(clauses)) if clauses else '', params


def search(f, sort='', page=1, under_path=None):
    where, params = _where(f, under_path=under_path)
    total = one(f'SELECT count(*) FROM taxon{where}', params)[0]
    q = (f.get('q') or '').strip().lower()
    key, desc = sort.lstrip('-'), sort.startswith('-')
    order_params = []
    if key in SORTS:
        order = ', '.join(f'{c} {"DESC" if desc else "ASC"}' for c in SORTS[key].split(', '))
    elif q:
        # exact name match, then prefix match, then substring; higher ranks first within each
        order = ('CASE WHEN lower(simple_name) = ? OR common_name_c = ? THEN 0 '
                 'WHEN lower(simple_name) LIKE ? OR common_name_c LIKE ? THEN 1 ELSE 2 END, depth, simple_name')
        order_params = [q, q, f'{q}%', f'{q}%']
    else:
        order = 'simple_name'
    sql = f'SELECT {LIST_COLS} FROM taxon{where} ORDER BY {order} LIMIT {PER_PAGE} OFFSET {(page - 1) * PER_PAGE}'
    return total, rows(sql, params + order_params)


def facet_counts(f, under_path=None, rank_limit=10):
    """Counts per facet value, each computed with every other active filter applied."""
    out = {}
    for name, col in FACETS.items():
        where, params = _where(f, skip=name, under_path=under_path)
        cond = f'{col} IS NOT NULL'
        sql = (f'SELECT {col} AS v, count(*) AS n FROM taxon{where} {"AND" if where else "WHERE"} {cond} '
               f'GROUP BY {col} ORDER BY n DESC')
        if name == 'rank':
            sql += f' LIMIT {rank_limit}'
        out[name] = [(str(r['v']), r['n']) for r in rows(sql, params)]
    # common groups: one pass, one conditional count per group
    where, params = _where(f, skip='group', under_path=under_path)
    conds = [(key, *_group_cond([key])) for key, *_ in groups.GROUPS]
    sums = ', '.join(f'sum(CASE WHEN {c} THEN 1 ELSE 0 END)' for _, c, _ in conds)
    counts = one(f'SELECT {sums} FROM taxon{where}', [x for _, _, cp in conds for x in cp] + params)
    out['group'] = [(key, n or 0) for (key, _, _), n in zip(conds, counts) if n]
    return out


def by_names(names):
    """Exact scientific-name lookup: {simple_name: [rows]} (a name can be a homonym across kingdoms)."""
    names, out = list(names), {}
    for i in range(0, len(names), 500):
        chunk = names[i:i + 500]
        for r in rows(f'SELECT {LIST_COLS}, depth FROM taxon WHERE simple_name IN ({",".join("?" * len(chunk))})', chunk):
            out.setdefault(r['simple_name'], []).append(r)
    return out
