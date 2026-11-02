#!/usr/bin/env python3
# Рисует график коммитов за год как изометрический ночной город (для README).
# Один день = одно здание, чем больше коммитов, тем больше этажей. Цвет крыши - состав резины как на 3D-странице.
# Дни без коммитов - трасса, лужайка или тротуар.
# Данные берём из docs/data/contributions.json, результат кладём в profile-3d-contrib/profile-city.svg
import datetime as dt
import json
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs', 'data', 'contributions.json')
DST = os.path.join(ROOT, 'profile-3d-contrib', 'profile-city.svg')

W, H = 1280, 830
STEP_X, STEP_Y = 17, 8.5   # расстояние между клетками на экране
HALF_X, HALF_Y = 15, 7.5   # половина размеров ромба здания
FLOOR_H = 5.5              # высота этажа в пикселях
MAX_FLOORS = 14

# состав резины: чем больше коммитов за день, тем твёрже (белая) шина на крыше
COMPOUNDS = [
    ('wet', '#1a8fff', 'Wet'),
    ('inter', '#25e060', 'Inter'),
    ('soft', '#ff2d2d', 'Soft'),
    ('medium', '#ffe01a', 'Medium'),
    ('hard', '#f2f2f7', 'Hard'),
]
GROUND = {'road': '#2b2d33', 'lawn': '#2f6b34', 'walk': '#6d6f78'}


def diamond(cx, cy, hx, hy):
    return f'{cx - hx},{cy} {cx},{cy - hy} {cx + hx},{cy} {cx},{cy + hy}'


def building(floors, seed):
    """Здание с центром основания в (0, 0): две стены с окнами. Крыша рисуется отдельно."""
    h = floors * FLOOR_H
    rnd = random.Random(seed)
    left = f'<polygon points="{-HALF_X},0 0,{HALF_Y} 0,{HALF_Y - h} {-HALF_X},{-h}" fill="#4a5a76"/>'
    right = f'<polygon points="0,{HALF_Y} {HALF_X},0 {HALF_X},{-h} 0,{HALF_Y - h}" fill="#37445c"/>'
    windows = ''
    for f in range(floors):
        for side in (-1, 1):
            for col in range(2):
                if rnd.random() < 0.5:
                    continue   # не во всех окнах горит свет
                x = (-HALF_X if side == -1 else 0) + 3 + col * 6.2
                # нижняя кромка стены: левая идёт вниз вправо, правая - вверх вправо
                edge = HALF_Y * (x + HALF_X) / HALF_X if side == -1 else HALF_Y * (1 - x / HALF_X)
                y = edge - f * FLOOR_H - 5.2
                windows += f'<rect x="{x:.1f}" y="{y:.1f}" width="3.4" height="2.6" fill="#ffd27a" opacity="{0.55 + rnd.random() * 0.45:.2f}"/>'
    return f'<g id="b{floors}">{left}{right}{windows}</g>'


def make_defs():
    defs = '<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#3a4bd0" stop-opacity=".22"/><stop offset="1" stop-color="#3a4bd0" stop-opacity="0"/></radialGradient>'
    for kind, color in GROUND.items():
        defs += f'<polygon id="g-{kind}" points="{diamond(0, 0, HALF_X + 1.5, HALF_Y + 0.8)}" fill="{color}"/>'
    for f in range(1, MAX_FLOORS + 4):
        defs += building(f, f * 17)
    for name, color, _ in COMPOUNDS:
        defs += f'<polygon id="r-{name}" points="{diamond(0, 0, HALF_X + 1, HALF_Y + 0.5)}" fill="{color}" stroke="#000" stroke-opacity=".35" stroke-width=".6"/>'
    return defs


def main():
    days = json.load(open(SRC, encoding='utf-8'))['days'][-365:]
    counts = {}
    for day, count in days:
        counts[dt.date.fromisoformat(day)] = count

    first, last = min(counts), max(counts)
    total = sum(counts.values())
    best = max(counts.values()) or 1
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)   # неделя с воскресенья, как на GitHub

    cells = []   # (неделя + день недели, неделя, день недели, коммиты, номер дня)
    day = start
    while day <= last:
        week, weekday = divmod((day - start).days, 7)
        cells.append((week + weekday, week, weekday, counts.get(day, 0), (day - start).days))
        day += dt.timedelta(days=1)

    weeks = cells[-1][1] + 1
    x0 = W / 2 - (-6 * STEP_X + (weeks - 1) * STEP_X) / 2
    y0 = 210 + MAX_FLOORS * FLOOR_H

    # рисуем от дальних клеток к ближним, чтобы высокие дома не перекрывали ближние неправильно
    picture = ''
    for _, week, weekday, count, n in sorted(cells):
        x = x0 + (week - weekday) * STEP_X
        y = y0 + (week + weekday) * STEP_Y
        if count == 0:
            kind = ('road', 'lawn', 'walk')[int(random.Random(n).random() * 10) % 3]
            picture += f'<use href="#g-{kind}" x="{x:.1f}" y="{y:.1f}"/>'
            continue
        picture += f'<use href="#g-walk" x="{x:.1f}" y="{y:.1f}"/>'
        k = math.sqrt(count / best)   # корень, чтобы один большой день не съедал остальные
        floors = 1 + round(k * (MAX_FLOORS - 1))
        name = COMPOUNDS[min(int(k * len(COMPOUNDS)), len(COMPOUNDS) - 1)][0]
        top = y - floors * FLOOR_H
        picture += f'<use href="#b{floors}" x="{x:.1f}" y="{y:.1f}"/><use href="#r-{name}" x="{x:.1f}" y="{top:.1f}"/>'

    stars = ''
    rnd = random.Random(7)
    for _ in range(90):
        stars += f'<circle cx="{rnd.random() * W:.0f}" cy="{rnd.random() * 230:.0f}" r="{0.5 + rnd.random() * 0.9:.1f}" fill="#fff" opacity="{0.25 + rnd.random() * 0.6:.2f}"/>'

    legend = ''
    for i, (_, color, name) in enumerate(COMPOUNDS):
        x = W - 56 - 4 * 104 - 70 + i * 104
        legend += f'<rect x="{x - 9}" y="68" width="18" height="12" fill="{color}"/>'
        legend += f'<text x="{x + 18}" y="79" font-size="14" fill="#86868b">{name}</text>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last year as a night city: one building per day, more commits means more floors">
<defs>{make_defs()}</defs>
<g font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
<rect width="{W}" height="{H}" fill="#070a16"/>
{stars}
<ellipse cx="{W / 2}" cy="{y0 + 150}" rx="640" ry="270" fill="url(#glow)"/>
<text x="56" y="84" font-size="56" font-weight="700" letter-spacing="-2" fill="#f5f5f7">{total}</text>
<text x="56" y="116" font-size="18" font-weight="500" fill="#86868b">contributions · {first:%b %-d, %Y} – {last:%b %-d, %Y}</text>
{picture}
{legend}
<text x="{W - 56}" y="116" font-size="14" text-anchor="end" fill="#86868b">more commits = more floors</text>
</g>
</svg>
'''
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(total, 'contributions,', len(cells), 'days')


if __name__ == '__main__':
    main()
