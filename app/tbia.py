"""Specimens with images from the TBIA data portal (https://tbiadata.tw/zh-hant/api/doc), cached in data/cache.sqlite."""
import json
import re
import time
import urllib.parse
import urllib.request

from flask import current_app

from .db import get_cache

API = 'https://tbiadata.tw/api/v1/occurrence'
TTL = 30 * 24 * 3600
LIMIT = 24  # specimens shown; the tab links to TBIA for the rest
FETCH = 100  # specimens looked at to pick those LIMIT from (TBIA lists GBIF's overseas copies first)
BLOCKED = ('oxalis.br.fgov.be',)  # image hosts that refuse other sites (403)
# smaller renditions some collections serve next to the full image: (pattern, replacement)
THUMBS = [
    (re.compile(r'^(https://brmas-media\.s3-ap-northeast-1\.amazonaws\.com/.*)-[lx]\.jpg$'), r'\1-m.jpg'),  # HAST, TAIF
    (re.compile(r'^(https://medialib\.naturalis\.nl/file/id/[^/]+/format/)large$'), r'\1medium'),
    (re.compile(r'^(https://media01\.symbiota\.org/.*)_lg\.jpg$'), r'\1_tn.jpg'),
    (re.compile(r'^(https://collections\.nmnh\.si\.edu/media/\?i=\d+)&h=\d+$'), r'\1&h=400'),
]


def _get(params):
    req = urllib.request.Request(f'{API}?{urllib.parse.urlencode(params)}',
                                 headers={'User-Agent': 'Species123 (+https://species123.naturedb.org; specimens)'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)


def thumb(url):
    for pattern, repl in THUMBS:
        if pattern.match(url):
            return pattern.sub(repl, url)
    return url


def _image(media):
    """The first usable image URL in associatedMedia (several are joined by ';' or '|'; IIIF manifests are not images)."""
    return next((u for u in (s.strip() for s in re.split(r'[;|]', media or ''))
                 if u.startswith('http') and 'manifest' not in u and not any(b in u for b in BLOCKED)), None)


def _collector(r):
    """Collector and number; a record number with letters in it already names the collector ("Liao, CC; et al. 437")."""
    number = (r.get('recordNumber') or '').strip()
    if re.search(r'[A-Za-z]', number):
        return number
    return ' '.join(x for x in [(r.get('recordedBy') or '').strip(), number] if x)


def _fetch(taxon_id):
    base = {'taxonID': taxon_id, 'isCollection': 'true'}
    total = _get({**base, 'limit': 1})['meta']['total']
    found = _get({**base, 'hasMedia': 'image', 'limit': FETCH}) if total else {'meta': {'total': 0}, 'data': []}
    items = []
    for r in found['data']:
        img = _image(r.get('associatedMedia'))
        if not img:
            continue
        items.append({
            'id': r['id'], 'image': img, 'thumb': thumb(img),
            'catalog': r.get('catalogNumber') or '', 'holder': r.get('rightsHolder') or '',
            'dataset': r.get('datasetName') or '', 'collector': _collector(r), 'date': r.get('standardDate') or r.get('eventDate') or '',
            'locality': r.get('locality') or r.get('county') or '', 'type_status': r.get('typeStatus') or '',
            'license': r.get('mediaLicense') or r.get('license') or '',
        })
    # Taiwan's own collections first, then images with a known small rendition (some others are 20 MB scans)
    items.sort(key=lambda s: (s['holder'] == 'GBIF', s['thumb'] == s['image']))
    return {'total': total, 'with_image': found['meta']['total'], 'items': items[:LIMIT]}


def specimens(taxon_id):
    """{'total': specimens on TBIA, 'with_image': those with images, 'items': up to LIMIT of them}.
    Empty on failure; misses are cached too."""
    cache = get_cache()
    hit = cache.execute('SELECT body, fetched_at FROM tbia_cache WHERE taxon_id = ?', (taxon_id,)).fetchone()
    if hit and time.time() - hit[1] < TTL:
        return json.loads(hit[0])
    try:
        data = _fetch(taxon_id)
    except Exception as e:
        current_app.logger.warning('TBIA specimens %s: %s', taxon_id, e)
        return json.loads(hit[0]) if hit else {'total': 0, 'with_image': 0, 'items': []}
    cache.execute('INSERT OR REPLACE INTO tbia_cache VALUES (?, ?, ?)', (taxon_id, json.dumps(data), time.time()))
    cache.commit()
    return data
