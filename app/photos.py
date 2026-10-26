"""Taxon photos from iNaturalist (openly licensed only), cached in data/cache.sqlite."""
import json
import time
import urllib.parse
import urllib.request

from flask import current_app

from .db import get_cache

API = 'https://api.inaturalist.org/v1'
TTL = 30 * 24 * 3600
MAX_PHOTOS = 5
THUMB_BATCH = 30  # iNaturalist ids per /taxa/{ids} request
NAME_LOOKUPS = 10  # gallery species looked up by name per page view (no iNat id, or no usable photo)
# TaiCOL kingdom -> iNaturalist kingdom taxon id; a hit must sit under the same kingdom
# (homonyms like Actaea the crab genus vs Actaea the plant genus)
INAT_KINGDOM = {'Animalia': 1, 'Plantae': 47126, 'Fungi': 47170, 'Chromista': 48222, 'Protozoa': 47686,
                'Bacteria': 67333, 'Archaea': 151817}


def _get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Species123 (+https://species123.naturedb.org; taxon photos)'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)


def _fetch(name, kingdom):
    kid = INAT_KINGDOM.get(kingdom)
    if kid is None:
        return {'inat_id': None, 'photos': []}
    found = _get(f'{API}/taxa?' + urllib.parse.urlencode({'q': name, 'per_page': 10, 'is_active': 'true'}))
    # only iNaturalist's own accepted name, identical to TaiCOL's accepted name — never a synonym hit
    match = next((r for r in found.get('results') or []
                  if r['name'] == name and r.get('is_active') and kid in (r.get('ancestor_ids') or [])), None)
    if not match:
        return {'inat_id': None, 'photos': []}
    detail = (_get(f'{API}/taxa/{match["id"]}').get('results') or [{}])[0]
    photos = []
    for tp in detail.get('taxon_photos') or []:
        p = tp.get('photo') or {}
        if not p.get('license_code') or not p.get('medium_url'):
            continue  # skip all-rights-reserved
        photos.append({
            'id': p['id'],
            'medium': p['medium_url'],
            'large': p['medium_url'].replace('/medium.', '/large.'),
            'attribution': p.get('attribution') or '',
            'license': p['license_code'].upper(),
            'page': f'https://www.inaturalist.org/photos/{p["id"]}',
        })
        if len(photos) == MAX_PHOTOS:
            break
    return {'inat_id': match['id'], 'photos': photos}


def taxon_photos(name, kingdom):
    """{'inat_id', 'photos': [...]} for a TaiCOL accepted name. Empty on failure; misses are cached too."""
    key = f'{kingdom}|{name}'
    cache = get_cache()
    hit = cache.execute('SELECT body, fetched_at FROM photo_cache WHERE name = ?', (key,)).fetchone()
    if hit and time.time() - hit[1] < TTL:
        return json.loads(hit[0])
    try:
        data = _fetch(name, kingdom)
    except Exception as e:
        current_app.logger.warning('iNaturalist photos %s: %s', name, e)
        return json.loads(hit[0]) if hit else {'inat_id': None, 'photos': []}
    cache.execute('INSERT OR REPLACE INTO photo_cache VALUES (?, ?, ?)', (key, json.dumps(data), time.time()))
    cache.commit()
    return data


def _photo(p):
    return {'square': p['square_url'], 'medium': p['medium_url'], 'attribution': p.get('attribution') or '',
            'license': p['license_code'].upper(), 'page': f'https://www.inaturalist.org/photos/{p["id"]}'}


def thumbs(inat_ids):
    """{inat_id: photo or None}: each iNaturalist taxon's default photo, else its first openly licensed one.
    Batched; misses cached too."""
    ids = list(dict.fromkeys(str(i) for i in inat_ids if i))
    cache = get_cache()
    out, stale = {}, {}
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        for inat_id, body, fetched in cache.execute(
                f'SELECT inat_id, body, fetched_at FROM thumb_cache WHERE inat_id IN ({",".join("?" * len(chunk))})', chunk):
            (out if time.time() - fetched < TTL else stale)[inat_id] = json.loads(body)
    todo = [i for i in ids if i not in out]
    for i in range(0, len(todo), THUMB_BATCH):
        batch = todo[i:i + THUMB_BATCH]
        try:
            found = {str(r['id']): r for r in _get(f'{API}/taxa/' + ','.join(batch)).get('results') or []}
        except Exception as e:
            current_app.logger.warning('iNaturalist thumbs: %s', e)
            out.update({b: stale.get(b) for b in batch})
            continue
        now = time.time()
        for b in batch:
            r = found.get(b) or {}
            # the default photo, else the first openly licensed one of the taxon's photos
            ok = [p for p in [r.get('default_photo') or {}] + [tp.get('photo') or {} for tp in r.get('taxon_photos') or []]
                  if p.get('license_code') and p.get('square_url') and p.get('medium_url')]
            out[b] = _photo(ok[0]) if ok else None
            cache.execute('INSERT OR REPLACE INTO thumb_cache VALUES (?, ?, ?)', (b, json.dumps(out[b]), now))
        cache.commit()
    return out
