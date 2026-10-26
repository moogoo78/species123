"""Draw the WGSRPD level-3 "botanical countries" as one SVG world map: app/static/wgsrpd-l3.svg.

    python scripts/build_wgsrpd_svg.py level3.geojson

level3.geojson is from https://github.com/tdwg/wgsrpd (geojson/level3.geojson). Each region is a
<path data-code="TAI"> (plate carrée, 2 px per degree, 84°N–61°S); regions with too little land to see
(small islands, even when spread out like the Ryukyus) get a <circle> marker with the same data-code. The species page colours them from WCVP's distribution.
"""
import json
import sys
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'app' / 'static' / 'wgsrpd-l3.svg'
SCALE = 2  # px per degree
TOP, BOTTOM = 84, -61
STEP = 0.5  # px grid points are snapped to; consecutive repeats are dropped
DOT = 8  # px²: regions with less land than this get a marker


def xy(lon, lat):
    return round((lon + 180) * SCALE / STEP) * STEP, round((TOP - lat) * SCALE / STEP) * STEP


def num(v):
    return f'{v:g}'.replace('0.', '.', 1) if abs(v) < 1 else f'{v:g}'


def rel(pts):
    """Relative path data: M x y, then l dx dy steps (shorter than absolute points)."""
    out = [f'M{num(pts[0][0])} {num(pts[0][1])}l']
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for v in (x1 - x0, y1 - y0):
            s = num(v)
            out.append(s if s[0] == '-' or out[-1][-1] == 'l' else ' ' + s)
    return ''.join(out) + 'z'


def area(pts):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def ring_path(ring):
    pts = []
    for lon, lat in ring:
        p = xy(lon, lat)
        if not pts or p != pts[-1]:
            pts.append(p)
    if len(set(pts)) < 3:
        return '', pts
    return rel(pts), pts


def main(src):
    feats = json.loads(Path(src).read_text())['features']
    out = []
    for f in sorted(feats, key=lambda f: f['properties']['LEVEL3_COD']):
        code, name = f['properties']['LEVEL3_COD'], f['properties']['LEVEL3_NAM']
        geom = f['geometry']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        d, allpts, land = [], [], 0
        for poly in polys:
            for i, ring in enumerate(poly):
                p, pts = ring_path(ring)
                allpts += pts
                land += area(pts) if i == 0 else -area(pts)  # holes after the outer ring
                if p:
                    d.append(p)
        xs, ys = [p[0] for p in allpts], [p[1] for p in allpts]
        title = f'<title>{escape(name)}</title>'
        if d:
            out.append(f'<path data-code="{code}" d="{"".join(d)}">{title}</path>')
        if land < DOT:
            cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
            out.append(f'<circle class="dot" data-code="{code}" cx="{num(cx)}" cy="{num(cy)}" r="2.5">{title}</circle>')
    w, h = 360 * SCALE, (TOP - BOTTOM) * SCALE
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">\n' + '\n'.join(out) + '\n</svg>\n')
    print(f'wrote {OUT} ({OUT.stat().st_size // 1024} KB, {len(feats)} regions)')


if __name__ == '__main__':
    main(sys.argv[1])
