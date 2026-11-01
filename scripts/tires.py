#!/usr/bin/env python3
# Рисует график коммитов за год стопками шин Формулы 1 (для README).
# Данные берём из docs/data/contributions.json, результат кладём в profile-3d-contrib/profile-tires.svg
import datetime as dt
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs', 'data', 'contributions.json')
DST = os.path.join(ROOT, 'profile-3d-contrib', 'profile-tires.svg')

W, H = 1280, 760
STEP_X, STEP_Y = 17, 8.5   # расстояние между клетками на экране
RX, RY = 14.5, 7.25        # размеры эллипса шины
TIRE_H = 6.5               # высота одной шины
MAX_TIRES = 8              # выше 8 шин в стопке не рисуем

# состав резины по ресурсу: мало коммитов за день - шина "живёт" недолго (дождевая, софт),
# много коммитов - долгоиграющий хард
COMPOUNDS = [
    ('wet', '#0a84ff', 'Wet'),
    ('inter', '#30d158', 'Inter'),
    ('soft', '#ff3b30', 'Soft'),
    ('medium', '#ffd60a', 'Medium'),
    ('hard', '#f2f2f7', 'Hard'),
]


def ellipse(y, scale, extra):
    return f'<ellipse cy="{-y}" rx="{RX * scale:.2f}" ry="{RY * scale:.2f}" {extra}/>'


def tire(name, color, h):
    # бок шины
    svg = f'<path d="M{-RX} {-h}V0A{RX} {RY} 0 0 0 {RX} 0V{-h}Z" fill="url(#rubber)"/>'
    # две канавки, у плоской шины их нет
    if h > 3:
        for part in (0.33, 0.66):
            y = -h * part
            svg += f'<path d="M{-RX} {y:.2f}A{RX} {RY} 0 0 0 {RX} {y:.2f}" fill="none" stroke="#000" stroke-opacity=".55" stroke-width=".8"/>'
    # верх: резина, цветное кольцо, диск и дырка
    svg += ellipse(h, 1, 'fill="#17171a"')
    svg += ellipse(h, 0.8, f'fill="none" stroke="{color}" stroke-width="2.2"')
    svg += ellipse(h, 0.5, 'fill="#3a3a3e"')
    svg += ellipse(h, 0.26, 'fill="#050506"')
    return f'<g id="{name}">{svg}</g>'


def get_defs():
    defs = ('<linearGradient id="rubber" x1="0" x2="1" y1="0" y2="0">'
            '<stop offset="0" stop-color="#4a4a50"/><stop offset=".4" stop-color="#26262a"/>'
            '<stop offset="1" stop-color="#0d0d0f"/></linearGradient>'
            '<radialGradient id="glow" cx=".5" cy=".5" r=".5">'
            '<stop offset="0" stop-color="#ff375f" stop-opacity=".14"/>'
            '<stop offset="1" stop-color="#ff375f" stop-opacity="0"/></radialGradient>')
    for name, color, _ in COMPOUNDS:
        defs += tire('t-' + name, color, TIRE_H)
    defs += tire('t-flat', '#6e6e73', 2)   # день без коммитов
    # готовые стопки из 1..8 шин каждого состава, дальше на них просто ссылаемся через <use>
    for name, _, _ in COMPOUNDS:
        for n in range(1, MAX_TIRES + 1):
            stack = ''
            for j in range(n):
                stack += f'<use href="#t-{name}" y="{-j * TIRE_H:.2f}"/>'
            defs += f'<g id="s-{name}-{n}">{stack}</g>'
    return defs


def main():
    days = json.load(open(SRC, encoding='utf-8'))['days'][-365:]
    counts = {}
    for day, count in days:
        counts[dt.date.fromisoformat(day)] = count

    first, last = min(counts), max(counts)
    total = sum(counts.values())
    best = max(counts.values()) or 1
    # неделя начинается с воскресенья, как на GitHub
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)

    # (номер недели + день недели, номер недели, день недели, коммиты)
    cells = []
    day = start
    while day <= last:
        week, weekday = divmod((day - start).days, 7)
        cells.append((week + weekday, week, weekday, counts.get(day, 0)))
        day += dt.timedelta(days=1)

    weeks = cells[-1][1] + 1
    x0 = W / 2 - (-6 * STEP_X + (weeks - 1) * STEP_X) / 2
    y0 = 190 + MAX_TIRES * TIRE_H

    # рисуем от дальних клеток к ближним, чтобы стопки не перекрывали друг друга неправильно
    picture = ''
    for _, week, weekday, count in sorted(cells):
        x = x0 + (week - weekday) * STEP_X
        y = y0 + (week + weekday) * STEP_Y
        if count == 0:
            picture += f'<use href="#t-flat" x="{x:.1f}" y="{y:.1f}"/>'
            continue
        k = math.sqrt(count / best)   # корень, чтобы один большой день не съедал остальные
        n = 1 + round(k * (MAX_TIRES - 1))
        name = COMPOUNDS[min(int(k * len(COMPOUNDS)), len(COMPOUNDS) - 1)][0]
        picture += f'<use href="#s-{name}-{n}" x="{x:.1f}" y="{y:.1f}"/>'

    legend = ''
    for i, (_, color, name) in enumerate(COMPOUNDS):
        x = W - 56 - 4 * 104 - 70 + i * 104
        legend += f'<ellipse cx="{x}" cy="76" rx="11" ry="5.5" fill="#17171a" stroke="{color}" stroke-width="2.2"/>'
        legend += f'<text x="{x + 18}" y="81" font-size="14" fill="#86868b">{name}</text>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last year as stacks of Formula 1 tires">
<defs>{get_defs()}</defs>
<g font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
<rect width="{W}" height="{H}" fill="#000"/>
<ellipse cx="{W / 2}" cy="{y0 + 150}" rx="620" ry="260" fill="url(#glow)"/>
<text x="56" y="84" font-size="56" font-weight="700" letter-spacing="-2" fill="#f5f5f7">{total}</text>
<text x="56" y="116" font-size="18" font-weight="500" fill="#86868b">contributions · {first:%b %-d, %Y} – {last:%b %-d, %Y}</text>
{picture}
{legend}
<text x="{W - 56}" y="116" font-size="14" text-anchor="end" fill="#86868b">more commits = more tires</text>
</g>
</svg>
'''
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(total, 'contributions,', len(cells), 'days')


if __name__ == '__main__':
    main()
