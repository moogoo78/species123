"""Scrape OCA's 臺灣百種海洋生物-大型海藻與海草 species pages into scraper/oca-seagrass.csv.

    python scraper/oca_seagrass.py fetch   # list + detail pages into data/oca-seagrass/ (resumable)
    python scraper/oca_seagrass.py build   # parse data/oca-seagrass/ into scraper/oca-seagrass.csv
    python scraper/oca_seagrass.py         # both

Fields are described in scraper/oca-seagrass.md. The site merges 生態習性 and
棲地分布 under one heading, so they share the ecology_habitat column. Pages
already on disk are skipped; delete data/oca-seagrass/ to force a fresh download.
"""
import csv
import html
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = 'https://www.oca.gov.tw/ch/home.jsp'
MENU = {'id': '535', 'parentpath': '0,298'}
DATA = Path(os.environ.get('SPECIES123_DATA', Path(__file__).resolve().parent.parent / 'data'))
RAW = DATA / 'oca-seagrass'
OUT = Path(__file__).resolve().parent / 'oca-seagrass.csv'

SECTIONS = {'形態特徵': 'morphology', '生態習性與棲地分布': 'ecology_habitat', '補充資料': 'notes'}
SEAGRASS = {'Zostera', 'Thalassia', 'Halophila', 'Syringodium', 'Halodule', 'Cymodocea', 'Enhalus', 'Ruppia'}
FIELDS = ['dataserno', 'group', 'vernacular_name', 'scientific_name', 'other_common_name', 'english_common_name',
          'morphology', 'ecology_habitat', 'notes', 'url']

# www.oca.gov.tw serves an incomplete certificate chain, so verification fails.
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def detail_url(serno):
    return BASE + '?' + urllib.parse.urlencode({**MENU, 'mcustomize': 'ocamaritime_view.jsp', 'dataserno': serno}, safe=',')


def get(url, data=None):
    req = urllib.request.Request(url, data=data and urllib.parse.urlencode(data).encode(),
                                 headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
        return r.read().decode('utf-8')


def list_ids():
    # A pagesize above the total returns every species on one page.
    s = get(BASE + '?id=535&parentpath=0,298',
            {**MENU, 'mcustomize': 'ocamaritime_list.jsp', 'page': 1, 'pagesize': 1000, 'intpage': 1})
    ids = re.findall(r'dataserno=(\d+)" title=', s)
    return list(dict.fromkeys(ids))


def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    ids = list_ids()
    (RAW / 'ids.txt').write_text('\n'.join(ids) + '\n')
    print(f'{len(ids)} species', file=sys.stderr)
    for serno in ids:
        path = RAW / f'{serno}.html'
        if path.exists() and path.stat().st_size:
            continue
        path.write_text(get(detail_url(serno)), encoding='utf-8')
        time.sleep(0.3)


def parse(serno, s):
    body = re.search(r'<div class="editor">(.*?)</div>\s*</div>\s*</div>', s, re.S).group(1)
    t = re.sub(r'<br\s*/?>|</p>', '\n', body)
    t = html.unescape(re.sub(r'<[^>]+>', '', t)).replace('\xa0', ' ').replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    lines = [re.sub(r'\s+', ' ', l).strip() for l in t.split('\n')]
    lines = [l for l in lines if l]

    row = {'dataserno': serno, 'url': detail_url(serno)}
    head, cur = [], None
    for l in lines:
        m = re.match(r'^([^：:]{1,12}?)\s*[：:]\s*(.*)$', l)
        key = m and m.group(1)
        if key in SECTIONS:
            cur = SECTIONS[key]
            row[cur] = m.group(2)
        elif cur:
            row[cur] = (row[cur] + '\n' + l).strip()
        elif key == '俗名':
            # A few pages put 英名 on the same line as 俗名.
            other, _, eng = m.group(2).partition('英名：')
            row['other_common_name'] = other.strip()
            if eng:
                row['english_common_name'] = eng.strip()
        elif key == '英名':
            row['english_common_name'] = m.group(2)
        else:
            head.append(l)

    if len(head) == 1:  # name and scientific name on one line (滸苔)
        head = list(re.match(r'^(\S+)\s+([A-Z].*)$', head[0]).groups())
    if len(head) != 2:
        print(f'{serno}: unexpected header lines {head}', file=sys.stderr)
    row['vernacular_name'] = head[0] if head else ''
    row['scientific_name'] = head[1] if len(head) > 1 else ''
    genus = (row['scientific_name'].split() or [''])[0]
    row['group'] = '海草' if genus in SEAGRASS else '海藻'
    return row


def build():
    ids = (RAW / 'ids.txt').read_text().split()
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for serno in ids:
            w.writerow(parse(serno, (RAW / f'{serno}.html').read_text(encoding='utf-8')))
    print(f'wrote {len(ids)} rows to {OUT}', file=sys.stderr)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if cmd in ('fetch', 'all'):
        fetch()
    if cmd in ('build', 'all'):
        build()
