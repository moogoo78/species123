"""GBIF taxon key by name, for taxa Wikidata has no GBIF id for; cached in data/cache.sqlite."""
import json
import time
import urllib.parse
import urllib.request

from flask import current_app

from .db import get_cache

API = 'https://api.gbif.org/v1'
TTL = 30 * 24 * 3600


def _fetch(name, kingdom, rank):
    q = {'scientificName': name, 'kingdom': kingdom, 'strict': 'true'}
    if rank:
        q['rank'] = rank.upper()
    req = urllib.request.Request(f'{API}/species/match?' + urllib.parse.urlencode(q),
                                 headers={'User-Agent': 'Species123 (+https://species123.naturedb.org; GBIF links)'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        m = json.load(resp)
    # only an exact hit on GBIF's accepted name, identical to TaiCOL's accepted name, in the same kingdom
    if m.get('matchType') == 'EXACT' and m.get('status') == 'ACCEPTED' and m.get('canonicalName') == name \
            and m.get('kingdom') == kingdom:
        return m['usageKey']
    return None


def taxon_key(name, kingdom, rank=None):
    """GBIF usageKey for a TaiCOL accepted name, or None. Misses are cached too."""
    key = f'{kingdom}|{name}'
    cache = get_cache()
    hit = cache.execute('SELECT body, fetched_at FROM gbif_cache WHERE name = ?', (key,)).fetchone()
    if hit and time.time() - hit[1] < TTL:
        return json.loads(hit[0])
    try:
        usage = _fetch(name, kingdom, rank)
    except Exception as e:
        current_app.logger.warning('GBIF match %s: %s', name, e)
        return json.loads(hit[0]) if hit else None
    cache.execute('INSERT OR REPLACE INTO gbif_cache VALUES (?, ?, ?)', (key, json.dumps(usage), time.time()))
    cache.commit()
    return usage
