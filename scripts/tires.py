#!/usr/bin/env python3
"""Рисует график коммитов за последний год как изометрические стопки шин Формулы 1.

Берёт docs/data/contributions.json (его выгружает scripts/contributions.py) и пишет
profile-3d-contrib/profile-tires.svg. Высота стопки — число коммитов за день, цвет боковины —
состав резины: синий (дождевая) → зелёный (промежуточная) → белая (hard) → жёлтая (medium) → красная (soft).
"""
import datetime as dt
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs', 'data', 'contributions.json')
DST = os.path.join(ROOT, 'profile-3d-contrib', 'profile-tires.svg')

W, H = 1280, 760
PX, PY = 17, 8.5           # шаг клетки по экрану
RX, RY = 14.5, 7.25        # полуоси эллипса шины
TH = 6.5                   # высота одной шины
MAX_TIRES = 8
COMPOUNDS = [('wet', '#0a84ff', 'Wet'), ('inter', '#30d158', 'Inter'), ('hard', '#f2f2f7', 'Hard'),
             ('medium', '#ffd60a', 'Medium'), ('soft', '#ff3b30', 'Soft')]

days = json.load(open(SRC, encoding='utf-8'))['days'][-365:]
counts = {dt.date.fromisoformat(d): c for d, c in days}
first, last = min(counts), max(counts)
start = first - dt.timedelta(days=(first.weekday() + 1) % 7)   # неделя начинается с воскресенья, как на GitHub
top = max(counts.values()) or 1
total = sum(counts.values())


def compound(k):
    return COMPOUNDS[min(int(k * len(COMPOUNDS)), len(COMPOUNDS) - 1)][0]


def tire(cid, color, height):
    """Одна шина с центром основания в (0, 0): боковая поверхность, верхний торец, цветное кольцо, диск."""
    h = height
    body = (f'<path d="M{-RX} {-h}V0A{RX} {RY} 0 0 0 {RX} 0V{-h}Z" fill="url(#rubber)"/>')
    grooves = ''.join(f'<path d="M{-RX} {-h * f:.2f}A{RX} {RY} 0 0 0 {RX} {-h * f:.2f}" fill="none" stroke="#000" stroke-opacity=".55" stroke-width=".8"/>'
                      for f in (0.33, 0.66)) if h > 3 else ''
    topface = (f'<ellipse cy="{-h}" rx="{RX}" ry="{RY}" fill="#17171a"/>'
               f'<ellipse cy="{-h}" rx="{RX * 0.8:.2f}" ry="{RY * 0.8:.2f}" fill="none" stroke="{color}" stroke-width="2.2"/>'
               f'<ellipse cy="{-h}" rx="{RX * 0.5:.2f}" ry="{RY * 0.5:.2f}" fill="#3a3a3e"/>'
               f'<ellipse cy="{-h}" rx="{RX * 0.26:.2f}" ry="{RY * 0.26:.2f}" fill="#050506"/>')
    return f'<g id="{cid}">{body}{grooves}{topface}</g>'


defs = ['<linearGradient id="rubber" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#4a4a50"/>'
        '<stop offset=".4" stop-color="#26262a"/><stop offset="1" stop-color="#0d0d0f"/></linearGradient>',
        '<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ff375f" stop-opacity=".14"/>'
        '<stop offset="1" stop-color="#ff375f" stop-opacity="0"/></radialGradient>']
for cid, color, _ in COMPOUNDS:
    defs.append(tire(f't-{cid}', color, TH))
defs.append(tire('t-flat', '#6e6e73', 2))
for cid, _, _ in COMPOUNDS:   # стопки из n шин одного состава
    for n in range(1, MAX_TIRES + 1):
        uses = ''.join(f'<use href="#t-{cid}" y="{-j * TH:.2f}"/>' for j in range(n))
        defs.append(f'<g id="s-{cid}-{n}">{uses}</g>')

cells = []
d = start
while d <= last:
    w, dow = (d - start).days // 7, (d - start).days % 7
    cells.append((w + dow, w, dow, counts.get(d, 0)))
    d += dt.timedelta(days=1)
weeks = max(c[1] for c in cells) + 1
min_x, max_x = -6 * PX, (weeks - 1) * PX
ox = W / 2 - (min_x + max_x) / 2
oy = 190 + MAX_TIRES * TH

body = []
for _, w, dow, c in sorted(cells):
    x, y = ox + (w - dow) * PX, oy + (w + dow) * PY
    if c == 0:
        body.append(f'<use href="#t-flat" x="{x:.1f}" y="{y:.1f}"/>')
        continue
    k = math.sqrt(c / top)
    n = 1 + round(k * (MAX_TIRES - 1))
    body.append(f'<use href="#s-{compound(k)}-{n}" x="{x:.1f}" y="{y:.1f}"/>')

legend = []
lx = W - 56 - 4 * 104 - 70
for i, (cid, color, name) in enumerate(COMPOUNDS):
    x = lx + i * 104
    legend.append(f'<ellipse cx="{x}" cy="76" rx="11" ry="5.5" fill="#17171a" stroke="{color}" stroke-width="2.2"/>'
                  f'<text x="{x + 18}" y="81" font-size="14" fill="#86868b">{name}</text>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last year as stacks of Formula 1 tires">
<defs>{''.join(defs)}</defs>
<g font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
<rect width="{W}" height="{H}" fill="#000"/>
<ellipse cx="{W / 2}" cy="{oy + 150}" rx="620" ry="260" fill="url(#glow)"/>
<text x="56" y="84" font-size="56" font-weight="700" letter-spacing="-2" fill="#f5f5f7">{total}</text>
<text x="56" y="116" font-size="18" font-weight="500" fill="#86868b">contributions · {first:%b %-d, %Y} – {last:%b %-d, %Y}</text>
{''.join(body)}
{''.join(legend)}
<text x="{W - 56}" y="116" font-size="14" text-anchor="end" fill="#86868b">more commits = more tires</text>
</g>
</svg>
'''
os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, 'w', encoding='utf-8').write(svg)
print(f'{DST}: {len(svg) // 1024} KB, {len(cells)} days, {total} contributions')
