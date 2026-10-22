"""Import TaiCOL accepted taxa (accepted names only — no synonyms) into data/taien.sqlite.

    python scripts/import_taicol.py fetch   # page api.taicol.tw/v2/taxon into data/raw/ (resumable)
    python scripts/import_taicol.py build   # build data/taien.sqlite from data/raw/
    python scripts/import_taicol.py         # both

The API caps pages at 300 rows, so a full fetch is ~460 requests. Pages already
on disk are skipped; delete data/raw/ to force a fresh download.
"""
import json
import os
import sqlite3
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

API = 'https://api.taicol.tw/v2/taxon'
PAGE = 300
DATA = Path(os.environ.get('TAIEN_DATA', Path(__file__).resolve().parent.parent / 'data'))
RAW = DATA / 'raw'
DB = DATA / 'taien.sqlite'

# Ranks counted in taxon_rank_count (node stat tiles) and used for sorting.
MAJOR_RANKS = ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species']
INFRA_RANKS = {'Subspecies', 'Variety', 'Form', 'Subvariety', 'Subform', 'Special Form', 'Race', 'Stirps', 'Morph', 'Aberration', 'Hybrid Formula'}

SCHEMA = """
CREATE TABLE taxon (
  taxon_id TEXT PRIMARY KEY,
  name_id INTEGER,
  rank TEXT,
  simple_name TEXT,
  name_author TEXT,
  formatted_name TEXT,
  common_name_c TEXT,
  alternative_name_c TEXT,
  kingdom TEXT,
  parent_id TEXT,
  depth INTEGER,
  path TEXT,
  is_hybrid INTEGER,
  is_endemic INTEGER,
  is_in_taiwan INTEGER,
  alien_type TEXT,
  alien_status_note TEXT,
  is_fossil INTEGER,
  is_terrestrial INTEGER,
  is_freshwater INTEGER,
  is_brackish INTEGER,
  is_marine INTEGER,
  cites TEXT,
  iucn TEXT,
  redlist TEXT,
  protected TEXT,
  sensitive TEXT,
  created_at TEXT,
  updated_at TEXT,
  n_children INTEGER DEFAULT 0,
  n_species INTEGER DEFAULT 0,
  family TEXT,
  family_c TEXT,
  genus TEXT,
  search_text TEXT
);
CREATE TABLE taxon_rank_count (taxon_id TEXT, rank TEXT, n INTEGER, PRIMARY KEY (taxon_id, rank));
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
"""

INDEXES = """
CREATE INDEX ix_taxon_parent ON taxon(parent_id, simple_name);
CREATE INDEX ix_taxon_rank ON taxon(rank);
CREATE INDEX ix_taxon_kingdom ON taxon(kingdom);
CREATE INDEX ix_taxon_updated ON taxon(updated_at);
CREATE INDEX ix_taxon_name ON taxon(simple_name);
CREATE INDEX ix_taxon_genus ON taxon(genus);
"""

COLUMNS = ['taxon_id', 'name_id', 'rank', 'simple_name', 'name_author', 'formatted_name', 'common_name_c',
           'alternative_name_c', 'kingdom',
           'is_hybrid', 'is_endemic', 'is_in_taiwan', 'alien_type', 'alien_status_note', 'is_fossil', 'is_terrestrial',
           'is_freshwater', 'is_brackish', 'is_marine', 'cites', 'iucn', 'redlist', 'protected', 'sensitive',
           'created_at', 'updated_at']


def get_json(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TaiEN importer'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.load(resp)
            if data.get('status', {}).get('code') == 200:
                return data
            raise RuntimeError(data.get('status'))
        except Exception as e:  # network hiccups / 5xx: back off and retry
            if i == tries - 1:
                raise
            wait = 5 * (i + 1)
            print(f'  retry in {wait}s ({e})', flush=True)
            time.sleep(wait)


def fetch_range(offset, limit):
    """Rows [offset, offset+limit). Some records make the API return 500 for every page that
    contains them, so a failing page is split in halves down to single rows, which are skipped."""
    try:
        return get_json(f'{API}?limit={limit}&offset={offset}', tries=3 if limit > 1 else 2)['data']
    except Exception as e:
        if limit == 1:
            print(f'  SKIP offset {offset}: {e}', flush=True)
            with open(RAW / 'skipped.txt', 'a') as f:
                f.write(f'{offset}\t{e}\n')
            return []
        half = limit // 2
        print(f'  splitting offset {offset} limit {limit}', flush=True)
        return fetch_range(offset, half) + fetch_range(offset + half, limit - half)


def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    total = get_json(f'{API}?limit=1&offset=0')['info']['total']
    print(f'TaiCOL reports {total} taxa', flush=True)
    for offset in range(0, total, PAGE):
        out = RAW / f'taxon-{offset:07d}.json'
        if out.exists():
            continue
        page = fetch_range(offset, min(PAGE, total - offset))
        tmp = out.with_suffix('.part')
        tmp.write_text(json.dumps(page, ensure_ascii=False))
        tmp.replace(out)
        print(f'  {offset + PAGE}/{total}', flush=True)
    (RAW / 'fetched_at.txt').write_text(datetime.now(timezone.utc).isoformat(timespec='seconds'))


def flag(v):
    return None if v is None else int(bool(v))


def build():
    pages = sorted(RAW.glob('taxon-*.json'))
    if not pages:
        sys.exit('no pages in data/raw — run "fetch" first')
    rows = {}
    for p in pages:
        for t in json.loads(p.read_text()):
            if t.get('taxon_status') == 'accepted':
                rows[t['taxon_id']] = t
    print(f'{len(rows)} accepted taxa from {len(pages)} pages', flush=True)

    # Tree: parent_taxon_id, falling back to the nearest higher_taxa entry we actually have.
    parent = {}
    for tid, t in rows.items():
        p = t.get('parent_taxon_id')
        if p not in rows:
            p = next((h['taxon_id'] for h in (t.get('higher_taxa') or [])[1:] if h['taxon_id'] in rows and h['taxon_id'] != tid), None)
        parent[tid] = p

    path = {}

    def path_of(tid):
        # iterative walk; guards against cycles in upstream data
        chain, seen, cur = [], set(), tid
        while cur and cur not in path and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            cur = parent.get(cur)
        base = path[cur] if cur in path else []
        for node in reversed(chain):
            base = base + [node]
            path[node] = base
        return path[tid]

    n_children = defaultdict(int)
    n_species = defaultdict(int)
    rank_count = defaultdict(int)
    for tid, t in rows.items():
        pth = path_of(tid)
        if parent[tid]:
            n_children[parent[tid]] += 1
        for anc in pth[:-1]:
            if t['rank'] in MAJOR_RANKS:
                rank_count[(anc, t['rank'])] += 1
        if t['rank'] == 'Species':
            for anc in pth:
                n_species[anc] += 1

    tmp = DB.with_suffix('.sqlite.tmp')
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    cols = COLUMNS + ['parent_id', 'depth', 'path', 'n_children', 'n_species', 'family', 'family_c', 'genus', 'search_text']
    sql = f'INSERT INTO taxon ({",".join(cols)}) VALUES ({",".join("?" * len(cols))})'
    bools = {'is_hybrid', 'is_endemic', 'is_in_taiwan', 'is_fossil', 'is_terrestrial', 'is_freshwater', 'is_brackish', 'is_marine'}

    def nearest(tid, rank):
        return next((rows[a] for a in reversed(path[tid]) if rows[a]['rank'] == rank), None)

    def values(tid, t):
        v = [flag(t.get(c)) if c in bools else t.get(c) for c in COLUMNS]
        fam, gen = nearest(tid, 'Family'), nearest(tid, 'Genus')
        # accepted scientific name + Chinese names only; synonyms / misapplied names are not searchable
        search = ' '.join(x for x in [t['simple_name'], t.get('common_name_c'), t.get('alternative_name_c')] if x)
        return v + [parent[tid], len(path[tid]) - 1, ','.join(path[tid]), n_children[tid], n_species[tid],
                    fam and fam['simple_name'], fam and fam.get('common_name_c'), gen and gen['simple_name'], search.lower()]

    con.executemany(sql, (values(tid, t) for tid, t in rows.items()))
    con.executemany('INSERT INTO taxon_rank_count VALUES (?,?,?)', ((a, r, n) for (a, r), n in rank_count.items()))
    fetched = (RAW / 'fetched_at.txt').read_text().strip() if (RAW / 'fetched_at.txt').exists() else ''
    con.executemany('INSERT INTO meta VALUES (?,?)', [
        ('source', API), ('fetched_at', fetched), ('built_at', datetime.now(timezone.utc).isoformat(timespec='seconds')),
        ('taxa', str(len(rows))),
    ])
    con.executescript(INDEXES)
    con.commit()
    con.execute('VACUUM')
    con.close()
    tmp.replace(DB)
    print(f'wrote {DB}', flush=True)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if cmd in ('fetch', 'all'):
        fetch()
    if cmd in ('build', 'all'):
        build()
