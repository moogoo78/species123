"""SQL against the read-only TaiCOL snapshot."""
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


def roots():
    return rows(f'SELECT {LIST_COLS}, n_children FROM taxon WHERE parent_id IS NULL AND n_children > 0 ORDER BY simple_name')


def rank_counts(taxon_id):
    return {r['rank']: r['n'] for r in rows('SELECT rank, n FROM taxon_rank_count WHERE taxon_id = ?', (taxon_id,))}


def kingdoms():
    return rows(f"SELECT {LIST_COLS} FROM taxon WHERE rank = 'Kingdom' AND n_species > 0 ORDER BY n_species DESC")


def recent(limit=8):
    return rows(f"SELECT {LIST_COLS} FROM taxon WHERE rank = 'Species' ORDER BY updated_at DESC, simple_name LIMIT ?", (limit,))


def siblings(t, exclude, limit=6):
    """Taxa sharing t's parent (e.g. same genus), for compare suggestions."""
    if not t['parent_id']:
        return []
    marks = ','.join('?' * len(exclude))
    return rows(f'SELECT {LIST_COLS} FROM taxon WHERE parent_id = ? AND taxon_id NOT IN ({marks}) '
                'ORDER BY simple_name LIMIT ?', (t['parent_id'], *exclude, limit))


def _where(f, skip=None, under_path=None):
    clauses, params = [], []
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
    return out
