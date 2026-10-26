"""Pick the WCVP (World Checklist of Vascular Plants) facts the site shows into data/raw/wcvp.json.

    python scripts/import_wcvp.py [wcvp dir]    # default data/wcvp/

The directory holds the WCVP download (wcvp_names.csv, wcvp_distribution.csv; https://sftp.kew.org/pub/data-repositories/WCVP/)
and taicol-wcvp-mapping.csv from match_wcvp.py, which maps TaiCOL accepted vascular plants to WCVP names.
Taxa whose match is ambiguous, missing, or only an Unplaced WCVP name are left out.
Per taxon: the WCVP accepted name it resolves to, POWO / IPNI ids, life form, climate, the range summary, and
the WGSRPD level-3 distribution. import_taicol.py build loads the result into the wcvp / wcvp_dist tables.
"""
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(os.environ.get('SPECIES123_DATA', Path(__file__).resolve().parent.parent / 'data'))
# mapping match types that reach a WCVP accepted name
MATCHED = {'accepted', 'accepted_simple', 'wcvp_synonym', 'stemmed', 'taicol_synonym'}


def read(path, delimiter='|'):
    return csv.DictReader(open(path, encoding='utf-8-sig', newline=''), delimiter=delimiter)


def main(src):
    csv.field_size_limit(10 ** 9)
    taxa = {r['taicol_taxon_id']: r for r in read(src / 'taicol-wcvp-mapping.csv', ',')
            if r['match_type'] in MATCHED and r['wcvp_accepted_id']}
    want = defaultdict(list)  # WCVP accepted plant_name_id -> TaiCOL taxon ids
    for tid, r in taxa.items():
        want[r['wcvp_accepted_id']].append(tid)
    names = {d['plant_name_id']: d for d in read(src / 'wcvp_names.csv') if d['plant_name_id'] in want}
    dist = defaultdict(list)
    for d in read(src / 'wcvp_distribution.csv'):
        if d['plant_name_id'] in want:
            status = 'extinct' if d['extinct'] == '1' else 'doubtful' if d['location_doubtful'] == '1' \
                else 'introduced' if d['introduced'] == '1' else 'native'
            dist[d['plant_name_id']].append([d['area_code_l3'], d['area'], status])
    rows = []
    for tid, r in sorted(taxa.items()):
        n = names.get(r['wcvp_accepted_id'])
        if not n:
            continue
        rows.append({
            'taxon_id': tid, 'plant_name_id': n['plant_name_id'], 'match_type': r['match_type'],
            'name': n['taxon_name'], 'authors': n['taxon_authors'],
            'powo_id': n['powo_id'], 'ipni_id': n['ipni_id'],
            'lifeform': n['lifeform_description'].strip(), 'climate': n['climate_description'].strip(),
            'range': n['geographic_area'].strip(), 'dist': sorted(dist[n['plant_name_id']]),
        })
    out = DATA / 'raw' / 'wcvp.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'built_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'rows': rows},
                              ensure_ascii=False))
    print(f'wcvp: {len(rows)} TaiCOL taxa, {sum(len(r["dist"]) for r in rows)} distribution rows -> {out}', flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / 'wcvp')
