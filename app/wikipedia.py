"""Wikipedia intro for a taxon, found through its Wikidata item; cached in data/cache.sqlite."""
import json
import time
import urllib.parse
import urllib.request

from flask import current_app

from .db import get_cache

TTL = 30 * 24 * 3600
UA = {'User-Agent': 'Species123 (+https://species123.naturedb.org; descriptions)'}


def _get(url, **headers):
    req = urllib.request.Request(url, headers={**UA, **headers})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)


def _fetch(qid, lang):
    q = {'action': 'wbgetentities', 'ids': qid, 'props': 'sitelinks', 'sitefilter': 'zhwiki|enwiki', 'format': 'json'}
    links = (_get('https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode(q))
             .get('entities', {}).get(qid, {}).get('sitelinks') or {})
    # the page's language first, the other one as a fallback
    for wiki in (lang, 'en' if lang == 'zh' else 'zh'):
        title = (links.get(f'{wiki}wiki') or {}).get('title')
        if not title:
            continue
        s = _get(f'https://{wiki}.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(title.replace(' ', '_'), safe=''),
                 **({'Accept-Language': 'zh-tw'} if wiki == 'zh' else {}))
        if s.get('type') == 'standard' and s.get('extract'):
            return {'lang': wiki, 'title': s.get('title') or title, 'extract': s['extract'],
                    'url': s.get('content_urls', {}).get('desktop', {}).get('page')
                    or f'https://{wiki}.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'))}
    return None


def summary(qid, lang):
    """{'lang', 'title', 'extract', 'url'} from zh or en Wikipedia, page language first, or None. Misses are cached too."""
    key = f'{qid}|{lang}'
    cache = get_cache()
    hit = cache.execute('SELECT body, fetched_at FROM wiki_cache WHERE name = ?', (key,)).fetchone()
    if hit and time.time() - hit[1] < TTL:
        return json.loads(hit[0])
    try:
        data = _fetch(qid, lang)
    except Exception as e:
        current_app.logger.warning('Wikipedia %s: %s', qid, e)
        return json.loads(hit[0]) if hit else None
    cache.execute('INSERT OR REPLACE INTO wiki_cache VALUES (?, ?, ?)', (key, json.dumps(data), time.time()))
    cache.commit()
    return data
