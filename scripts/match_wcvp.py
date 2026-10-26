"""Map TaiCOL accepted vascular plants (genus and below) to WCVP: data/wcvp/taicol-wcvp-mapping.csv.

    python scripts/match_wcvp.py names   # data/wcvp/{taicol,wcvp}-names.txt: every name to parse
    # parse them with gnparser (https://github.com/gnames/gnparser), on the host:
    docker run --rm -i gnames/gognparser:latest -f compact -C -j 8 < data/wcvp/wcvp-names.txt > data/wcvp/wcvp-parsed.jsonl
    docker run --rm -i gnames/gognparser:latest -f compact -C -j 8 < data/wcvp/taicol-names.txt > data/wcvp/taicol-parsed.jsonl
    python scripts/match_wcvp.py match   # -> data/wcvp/taicol-wcvp-mapping.csv; then import_wcvp.py and import_taicol.py build

Reads the TaiCOL pages in data/raw/ and the WCVP download in data/wcvp/ (wcvp_names.csv, wcvp_distribution.csv).
Names are compared as gnparser -C canonical forms (no authors); names with an unparsed tail are left out. Match order, first hit wins:
  accepted        TaiCOL accepted name = a WCVP Accepted name
  accepted_simple same once rank markers are dropped (var. vs subsp. vs f.)
  wcvp_synonym    = a WCVP synonym / illegitimate / invalid / orthographic / misapplied name -> its WCVP accepted name
  stemmed         Latin-ending variants (oldhami/oldhamii) = a WCVP Accepted name
  taicol_synonym  a TaiCOL synonym of the taxon = a WCVP Accepted name
  wcvp_unplaced   only a WCVP Unplaced name (no accepted name in WCVP)
Same rank level only (genus with genus, species with species, infraspecific with infraspecific).
Several WCVP candidates: keep those in the TaiCOL family, then those with the same author; still several -> ambiguous.
TaiCOL non-vascular plants (algae, bryophytes) are out of WCVP's scope and are not listed.
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(os.environ.get('SPECIES123_DATA', Path(__file__).resolve().parent.parent / 'data'))
RAW, WCVP = DATA / 'raw', DATA / 'wcvp'
RANKS = {'Genus', 'Species', 'Subspecies', 'Variety', 'Form', 'Hybrid Formula'}
SYN_STATUS = {'Synonym', 'Illegitimate', 'Invalid', 'Orthographic', 'Misapplied'}
COLS = ['taicol_taxon_id', 'taicol_name', 'taicol_author', 'taicol_rank', 'taicol_family', 'taicol_common_name_c',
        'taicol_is_in_taiwan', 'taicol_is_endemic', 'taicol_alien_type', 'match_type',
        'wcvp_matched_id', 'wcvp_matched_name', 'wcvp_matched_authors', 'wcvp_matched_status',
        'wcvp_accepted_id', 'wcvp_accepted_name', 'wcvp_accepted_authors', 'wcvp_accepted_family', 'wcvp_accepted_rank',
        'same_accepted_name', 'wcvp_taiwan', 'ipni_id', 'powo_id', 'candidates']


def read_wcvp(name):
    return csv.DictReader(open(WCVP / name, encoding='utf-8', newline=''), delimiter='|')


def taicol_plants():
    """TaiCOL accepted plants at the matched ranks (all of Plantae; vascular ones are picked in match)."""
    for p in sorted(RAW.glob('taxon-*.json')):
        for r in json.loads(p.read_text(encoding='utf-8')):
            if r['kingdom'] == 'Plantae' and r['taxon_status'] == 'accepted' and r['rank'] in RANKS:
                yield r


def load_parsed(path):
    return {d['verbatim']: d for d in map(json.loads, open(path, encoding='utf-8'))}


def keys(d):
    """(full, simple, stemmed) canonical forms, each prefixed by the name's cardinality."""
    c = d.get('canonical') if d.get('parsed') and not d.get('tail') else None  # 'monstr. x' etc. would collapse to the species
    if not c:
        return (None, None, None)
    n = d.get('cardinality', 0)
    return tuple(f'{n}|{c[k]}' for k in ('full', 'simple', 'stemmed'))


def norm_author(a):
    return re.sub(r'[\s.]', '', (a or '').lower())


def split_names(v):
    return [s.strip() for s in (v or '').split(',') if s.strip()]


def names():
    tc = {r['simple_name'].strip() for r in taicol_plants()} | {s for r in taicol_plants() for s in split_names(r['synonyms'])}
    wc = {d['taxon_name'].strip() for d in read_wcvp('wcvp_names.csv')}
    for out, ns in (('taicol-names.txt', tc), ('wcvp-names.txt', wc)):
        (WCVP / out).write_text(''.join(n + '\n' for n in sorted(ns) if n), encoding='utf-8')
        print(f'{len(ns)} names -> {WCVP / out}', flush=True)


def match():
    # WCVP names and indexes: accepted / synonym-like / unplaced, by each canonical form
    wcvp_parsed = load_parsed(WCVP / 'wcvp-parsed.jsonl')
    wcvp = {}
    idx = defaultdict(lambda: defaultdict(set))
    for d in read_wcvp('wcvp_names.csv'):
        wcvp[d['plant_name_id']] = d
        st = d['taxon_status']
        kind = 'acc' if st in ('Accepted', 'Artificial Hybrid') else 'syn' if st in SYN_STATUS and d['accepted_plant_name_id'] \
            else 'unp' if st == 'Unplaced' else None
        if not kind:
            continue
        for form, key in zip(('full', 'simple', 'stemmed'), keys(wcvp_parsed.get(d['taxon_name'].strip(), {}))):
            if key:
                idx[f'{kind}_{form}'][key].add(d['plant_name_id'])

    # WCVP Taiwan (TAI) occurrence per accepted plant_name_id
    tai = {}
    for d in read_wcvp('wcvp_distribution.csv'):
        if d['area_code_l3'] == 'TAI':
            flags = ['introduced' if d['introduced'] == '1' else 'native']
            flags += [f for f in ('extinct', 'location_doubtful') if d[f] == '1']
            tai[d['plant_name_id']] = ' '.join(flags)

    def accepted_of(pid):
        r = wcvp[pid]
        return r['accepted_plant_name_id'] or pid if r['taxon_status'] in SYN_STATUS else pid

    def pick(cands, family, author):
        """One WCVP id from candidates, or (None, all) when it stays ambiguous."""
        cands = sorted(cands)
        if len(cands) == 1:
            return cands[0], []
        narrowed = cands
        for test in (lambda p: wcvp[accepted_of(p)]['family'] == family,
                     lambda p: norm_author(wcvp[p]['taxon_authors']) == norm_author(author)):
            kept = [p for p in narrowed if test(p)]
            if kept:
                narrowed = kept
            if len({accepted_of(p) for p in narrowed}) == 1:
                return narrowed[0], cands
        return None, cands

    taicol_parsed = load_parsed(WCVP / 'taicol-parsed.jsonl')
    flag = lambda v: '' if v is None else str(v).lower()
    out, skipped, n = WCVP / 'taicol-wcvp-mapping.csv', 0, 0
    with open(out, 'w', newline='', encoding='utf-8-sig') as fo:
        w = csv.DictWriter(fo, COLS)
        w.writeheader()
        for r in taicol_plants():
            higher = r.get('higher_taxa') or []
            if not any(h['simple_name'] == 'Tracheophyta' for h in higher):
                skipped += 1
                continue
            family = next((h['simple_name'] for h in higher if h['rank'] == 'Family'), '')
            full, simple, stemmed = keys(taicol_parsed.get(r['simple_name'].strip(), {}))
            syn_full = [keys(taicol_parsed.get(s, {}))[0] for s in split_names(r['synonyms'])]
            steps = [('accepted', 'acc_full', [full]), ('accepted_simple', 'acc_simple', [simple]),
                     ('wcvp_synonym', 'syn_full', [full]), ('stemmed', 'acc_stemmed', [stemmed]),
                     ('taicol_synonym', 'acc_full', syn_full), ('wcvp_unplaced', 'unp_full', [full])]
            match_type, pid, cands = 'none' if full else 'not_parsed', None, []
            for name, lvl, ks in steps if full else []:
                found = set().union(*(idx[lvl].get(k, set()) for k in ks if k))
                if found:
                    pid, cands = pick(found, family, r['name_author'])
                    match_type = name if pid else 'ambiguous'
                    break
            m = wcvp.get(pid, {})
            a = wcvp.get(accepted_of(pid), {}) if pid else {}
            w.writerow({
                'taicol_taxon_id': r['taxon_id'], 'taicol_name': r['simple_name'], 'taicol_author': r['name_author'] or '',
                'taicol_rank': r['rank'], 'taicol_family': family, 'taicol_common_name_c': r['common_name_c'] or '',
                'taicol_is_in_taiwan': flag(r['is_in_taiwan']), 'taicol_is_endemic': flag(r['is_endemic']),
                'taicol_alien_type': r['alien_type'] or '', 'match_type': match_type,
                'wcvp_matched_id': pid or '', 'wcvp_matched_name': m.get('taxon_name', ''),
                'wcvp_matched_authors': m.get('taxon_authors', ''), 'wcvp_matched_status': m.get('taxon_status', ''),
                'wcvp_accepted_id': a.get('plant_name_id', ''), 'wcvp_accepted_name': a.get('taxon_name', ''),
                'wcvp_accepted_authors': a.get('taxon_authors', ''), 'wcvp_accepted_family': a.get('family', ''),
                'wcvp_accepted_rank': a.get('taxon_rank', ''),
                'same_accepted_name': flag(a.get('taxon_name') == r['simple_name']) if a else '',
                'wcvp_taiwan': tai.get(a.get('plant_name_id'), 'absent') if a else '',
                'ipni_id': a.get('ipni_id', ''), 'powo_id': a.get('powo_id', ''),
                'candidates': ' '.join(cands) if not pid else ' '.join(c for c in cands if c != pid),
            })
            n += 1
    print(f'{n} vascular plants -> {out} ({skipped} non-vascular skipped)', flush=True)


if __name__ == '__main__':
    csv.field_size_limit(10 ** 9)
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'names':
        names()
    elif cmd == 'match':
        match()
    else:
        sys.exit(__doc__)
