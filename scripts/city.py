#!/usr/bin/env python3
# Рисует график коммитов за год как изометрический ночной город (для README).
# Один день = одно здание, чем больше коммитов, тем больше этажей. Цвет крыши - состав резины как на 3D-странице.
# Дни без коммитов - трасса, лужайка или тротуар. Вокруг квартала кольцевая трасса, по ней всё время едут болиды
# (анимация внутри SVG, GitHub проигрывает её прямо в README).
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

# кольцевая трасса вокруг квартала, размеры в клетках
TRACK_W = 1.6     # ширина
TRACK_GAP = 1.9   # от центра крайних клеток до оси трассы
TRACK_R = 1.5     # радиус поворотов по оси
LANE = 0.4        # две полосы: ось ± LANE, чтобы болиды обгоняли, а не проезжали друг сквозь друга
# 11 команд по 2 болида, цвета те же, что на 3D-странице: [корпус, акцент]
TEAMS = [
    ('#ff8000', '#111214'), ('#e8002d', '#f5f5f7'), ('#1e2a5a', '#e10600'), ('#c8ccd4', '#00d2be'),
    ('#0b6b52', '#cedc00'), ('#0a8fd1', '#ff87bc'), ('#1250c9', '#64c4ff'), ('#f5f5f7', '#2b4cff'),
    ('#6e7176', '#f50537'), ('#dfe1e5', '#d0021b'), ('#141518', '#e8e8e8'),
]
# корпус, акцент, полоса (+1 внешняя, -1 внутренняя), секунд на круг, где он на старте (доля круга).
# Первая машина команды едет по внешней полосе, вторая по внутренней: полосы с разной скоростью, поэтому идут обгоны
CARS = [(body, accent, 1 if k == 0 else -1, 14.0 if k == 0 else 14.8, (i + k / 2) / len(TEAMS))
        for i, (body, accent) in enumerate(TEAMS) for k in (0, 1)]


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
    for i, (body, accent, _, _, _) in enumerate(CARS):
        defs += car(i, body, accent)
    return defs


def car(i, color, accent):
    """Болид сверху, носом по +x, центр в (0, 0). Размеры в клетках."""
    wheels = ''.join(f'<rect x="{x}" y="{y}" width="{w}" height=".12" rx=".03" fill="#0d0d0f"/>'
                     for x, w in ((-.5, .26), (.24, .2)) for y in (-.27, .15))
    return (f'<g id="car{i}" transform="scale(1.25)">{wheels}'
            f'<rect x="-.65" y="-.25" width=".13" height=".5" fill="{accent}"/>'   # заднее антикрыло
            f'<polygon points="-.55,-.09 -.1,-.15 .15,-.15 .28,-.06 .58,-.035 .58,.035 .28,.06 .15,.15 -.1,.15 -.55,.09" fill="{color}"/>'
            f'<rect x=".55" y="-.26" width=".1" height=".52" fill="{accent}"/>'   # переднее антикрыло
            f'<ellipse cx=".05" rx=".09" ry=".05" fill="#111"/>'   # кокпит
            f'<rect x="-.69" y="-.03" width=".05" height=".06" fill="#ff3b30"/></g>')   # фонарь сзади


def ring(u0, v0, u1, v1, r):
    """Замкнутый контур со скруглёнными углами. Старт в середине ближней прямой, едем по +u."""
    return (f'M{(u0 + u1) / 2:.2f},{v1:.2f} H{u1 - r:.2f} A{r:.2f},{r:.2f} 0 0 0 {u1:.2f},{v1 - r:.2f} '
            f'V{v0 + r:.2f} A{r:.2f},{r:.2f} 0 0 0 {u1 - r:.2f},{v0:.2f} '
            f'H{u0 + r:.2f} A{r:.2f},{r:.2f} 0 0 0 {u0:.2f},{v0 + r:.2f} '
            f'V{v1 - r:.2f} A{r:.2f},{r:.2f} 0 0 0 {u0 + r:.2f},{v1:.2f} Z')


def corners(u0, v0, u1, v1, r):
    """Только четыре поворота того же контура - для поребриков."""
    return (f'M{u1 - r:.2f},{v1:.2f} A{r:.2f},{r:.2f} 0 0 0 {u1:.2f},{v1 - r:.2f} '
            f'M{u1:.2f},{v0 + r:.2f} A{r:.2f},{r:.2f} 0 0 0 {u1 - r:.2f},{v0:.2f} '
            f'M{u0 + r:.2f},{v0:.2f} A{r:.2f},{r:.2f} 0 0 0 {u0:.2f},{v0 + r:.2f} '
            f'M{u0:.2f},{v1 - r:.2f} A{r:.2f},{r:.2f} 0 0 0 {u0 + r:.2f},{v1:.2f}')


def race(weeks):
    """Трасса вокруг квартала и болиды на ней, в координатах сетки (u - неделя, v - день недели).
    Рисуется до города: дальнюю часть трассы закрывают дома, ближнюю ничто не перекрывает."""
    u0, v0 = -TRACK_GAP, -TRACK_GAP
    u1, v1 = weeks - 1 + TRACK_GAP, 6 + TRACK_GAP
    half = TRACK_W / 2

    def box(o):   # контур, раздвинутый на o клеток наружу (o < 0 - внутрь)
        return u0 - o, v0 - o, u1 + o, v1 + o, TRACK_R + o

    out = f'<path d="{ring(*box(0))}" fill="none" stroke="#2b2d33" stroke-width="{TRACK_W}"/>'
    for o in (-half + .06, half - .06):   # белые линии по кромкам
        out += f'<path d="{ring(*box(o))}" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width=".05"/>'
    for o in (-half + .09, half - .09):   # красно-белые поребрики в поворотах
        out += (f'<path d="{corners(*box(o))}" fill="none" stroke="#f2f2f7" stroke-width=".18"/>'
                f'<path d="{corners(*box(o))}" fill="none" stroke="#ff3b30" stroke-width=".18" stroke-dasharray=".25 .25"/>')
    um, rows = (u0 + u1) / 2, 6   # клетчатая линия старт-финиш
    for row in range(rows):
        for col in range(2):
            fill = '#f2f2f7' if (row + col) % 2 else '#0d0d0f'
            out += f'<rect x="{um - .2 + col * .2:.2f}" y="{v1 - half + row * TRACK_W / rows:.3f}" width=".2" height="{TRACK_W / rows:.3f}" fill="{fill}"/>'

    shadows, bodies = '', ''
    for i, (_, _, lane, lap, start) in enumerate(CARS):
        motion = (f'<animateMotion path="{ring(*box(lane * LANE))}" dur="{lap}s" begin="-{lap * start:.2f}s" '
                  f'repeatCount="indefinite" rotate="auto"/>')
        shadows += f'<ellipse rx=".9" ry=".38" fill="#000" opacity=".45">{motion}</ellipse>'
        bodies += f'<use href="#car{i}">{motion}</use>'
    # корпус чуть приподнят над тенью: сдвиг (-l, -l) в сетке - это ровно вверх на экране
    return out + shadows + f'<g transform="translate(-.12 -.12)">{bodies}</g>'


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
    y0 = 190 + MAX_FLOORS * FLOOR_H   # чуть выше, чтобы ближняя часть трассы влезла снизу

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

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last year as a night city: one building per day, more commits means more floors. Race cars lap the circuit around it">
<defs>{make_defs()}</defs>
<g font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
<rect width="{W}" height="{H}" fill="#070a16"/>
{stars}
<ellipse cx="{W / 2}" cy="{y0 + 150}" rx="640" ry="270" fill="url(#glow)"/>
<text x="56" y="84" font-size="56" font-weight="700" letter-spacing="-2" fill="#f5f5f7">{total}</text>
<text x="56" y="116" font-size="18" font-weight="500" fill="#86868b">contributions · {first:%b %-d, %Y} – {last:%b %-d, %Y}</text>
<g transform="matrix({STEP_X} {STEP_Y} {-STEP_X} {STEP_Y} {x0:.1f} {y0:.1f})">{race(weeks)}</g>
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
