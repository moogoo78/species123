"""Live TaiCOL API calls not covered by the bulk import, cached in data/cache.sqlite."""
import json
import time
import urllib.request

from flask import current_app

from .db import get_cache

API = 'https://api.taicol.tw/v2'
TTL = 30 * 24 * 3600


def references(name_id):
    """Literature for a name, newest first. Returns None if TaiCOL can't be reached and nothing is cached."""
    if not name_id:
        return []
    cache = get_cache()
    hit = cache.execute('SELECT body, fetched_at FROM ref_cache WHERE name_id = ?', (name_id,)).fetchone()
    if hit and time.time() - hit[1] < TTL:
        return json.loads(hit[0])
    try:
        req = urllib.request.Request(f'{API}/references?name_id={int(name_id)}', headers={'User-Agent': 'TaiEN'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.load(resp)
        if data.get('status', {}).get('code') != 200:
            raise RuntimeError(data.get('status'))
    except Exception as e:
        current_app.logger.warning('TaiCOL references %s: %s', name_id, e)
        return json.loads(hit[0]) if hit else None  # stale beats nothing
    refs = sorted(
        ({'citation': r['citation'], 'year': r.get('publish_year'), 'type': r.get('reference_type'),
          'status': r.get('usage_status'), 'reference_id': r.get('reference_id')}
         for r in data.get('data') or [] if not r.get('is_deleted') and r.get('citation')),
        key=lambda r: -(r['year'] or 0))
    cache.execute('INSERT OR REPLACE INTO ref_cache VALUES (?, ?, ?)', (name_id, json.dumps(refs, ensure_ascii=False), time.time()))
    cache.commit()
    return refs
