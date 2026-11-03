#!/usr/bin/env python3
# Рисует график коммитов за год как изометрический ночной город (для README).
# Один день = одно здание, чем больше коммитов, тем больше этажей. Цвет крыши - состав резины как на 3D-странице.
# Дни без коммитов - лужайка или тротуар, а по части из них петляет трасса: в город она заходит с востока,
# объезжает дома и поворачивает на пустых днях, а назад идёт главной прямой вдоль ближнего края.
# По ней всё время едут 22 болида (анимация внутри SVG, GitHub проигрывает её прямо в README).
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

# трасса, размеры в клетках. Такой же маршрут строит 3D-страница (docs/index.html, cityRoute), трассы совпадают
TRACK_W = 0.7        # ширина асфальта
CORNER_R = 0.5       # радиус поворота в городе: полклетки
OUTSIDE = 1.7        # главная прямая и боковые связки идут на столько клеток дальше крайних клеток квартала
SPEED = 10           # клеток в секунду на прямой, в повороте вдвое медленнее
TURN_COST, OUT_COST = 2, 6   # поиск маршрута: штраф за поворот и за клетку улицы за дальним краем (ряд -1)
# 11 команд по 2 болида, цвета те же, что на 3D-странице: [корпус, акцент]
TEAMS = [
    ('#ff8000', '#111214'), ('#e8002d', '#f5f5f7'), ('#1e2a5a', '#e10600'), ('#c8ccd4', '#00d2be'),
    ('#0b6b52', '#cedc00'), ('#0a8fd1', '#ff87bc'), ('#1250c9', '#64c4ff'), ('#f5f5f7', '#2b4cff'),
    ('#6e7176', '#f50537'), ('#dfe1e5', '#d0021b'), ('#141518', '#e8e8e8'),
]
CARS = [team for team in TEAMS for _ in (0, 1)]


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
    for i, (body, accent) in enumerate(CARS):
        defs += car(i, body, accent)
    return defs


def car(i, color, accent):
    """Болид сверху, носом по +x, центр в (0, 0). Размеры в клетках."""
    wheels = ''.join(f'<rect x="{x}" y="{y}" width="{w}" height=".12" rx=".03" fill="#0d0d0f"/>'
                     for x, w in ((-.5, .26), (.24, .2)) for y in (-.27, .15))
    return (f'<g id="car{i}" transform="scale(.7)">{wheels}'
            f'<rect x="-.65" y="-.25" width=".13" height=".5" fill="{accent}"/>'   # заднее антикрыло
            f'<polygon points="-.55,-.09 -.1,-.15 .15,-.15 .28,-.06 .58,-.035 .58,.035 .28,.06 .15,.15 -.1,.15 -.55,.09" fill="{color}"/>'
            f'<rect x=".55" y="-.26" width=".1" height=".52" fill="{accent}"/>'   # переднее антикрыло
            f'<ellipse cx=".05" rx=".09" ry=".05" fill="#111"/>'   # кокпит
            f'<rect x="-.69" y="-.03" width=".05" height=".06" fill="#ff3b30"/></g>')   # фонарь сзади


def city_route(weeks, busy):
    """Путь через город с востока на запад по дням без коммитов: как можно меньше поворотов, дома объезжаем.
    Ряд -1 - улица за дальним краем квартала, туда трасса уходит, только если иначе не проехать.
    Цены целые, поэтому Дейкстра идёт по корзинам - 3D-страница делает то же самое и находит такой же путь."""
    def cost(w, r):
        if w < 0:
            return 1   # выезд из города на запад
        if r < 0:
            return OUT_COST
        return None if (w, r) in busy else 1

    moves = ((-1, 0), (0, 1), (0, -1))   # на запад, к ближнему краю, к дальнему
    best, prev, buckets = {}, {}, []

    def push(state, d, frm):
        if d < best.get(state, d + 1):
            best[state], prev[state] = d, frm
            buckets.extend([] for _ in range(d + 1 - len(buckets)))
            buckets[d].append(state)

    for r in range(-1, 7):
        if cost(weeks - 1, r) is not None:
            push((weeks - 1, r, 0), cost(weeks - 1, r), None)
    for d in range(10 ** 6):
        for state in buckets[d]:
            if best[state] != d:
                continue
            w, r, k = state
            if w < 0:   # выехали на запад: собираем путь с конца
                path, state = [], prev[state]
                while state:
                    path.append(state[:2])
                    state = prev[state]
                return path[::-1]
            for nk, (dw, dr) in enumerate(moves):
                c = cost(w + dw, r + dr) if r + dr <= 6 and r + dr >= -1 else None
                if c is not None and k + nk != 3:   # 1 + 2: вверх сразу после вниз - разворот, нельзя
                    push((w + dw, r + dr, nk), d + c + (TURN_COST if nk != k else 0), state)


def circuit(weeks, route):
    """Углы замкнутой трассы: главная прямая с запада на восток вдоль ближнего края, связка к городу,
    город с востока на запад, связка обратно к главной прямой."""
    vs, ue, uw = 6 + OUTSIDE, weeks - 1 + OUTSIDE, -OUTSIDE
    pts = [(uw, vs), (ue, vs), (ue, route[0][1])] + route + [(uw, route[-1][1])]
    n = len(pts)
    return [p for i, p in enumerate(pts)
            if not (pts[i - 1][0] == p[0] == pts[(i + 1) % n][0] or pts[i - 1][1] == p[1] == pts[(i + 1) % n][1])]


def race(corners):
    """Трасса по углам и болиды на ней, в координатах сетки (u - неделя, v - день недели).
    Рисуется после земли, но до домов: ближние дома закрывают болиды, а дальние до них не достают."""
    n = len(corners)

    def unit(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        return dx / length, dy / length, length

    start = ((corners[0][0] + corners[1][0]) / 2, corners[0][1])   # старт-финиш посередине главной прямой
    d, kerbs, segs, cur = f'M{start[0]:.2f},{start[1]:.2f}', '', [], start
    for j in range(1, n + 1):
        i = j % n
        p = corners[i]
        ix, iy, l1 = unit(corners[i - 1], p)
        ox, oy, l2 = unit(p, corners[(i + 1) % n])
        r = min(1.0 if i < 2 else CORNER_R, l1 / 2, l2 / 2)   # концы главной прямой - поворот пошире
        a = (p[0] - ix * r, p[1] - iy * r)
        b = (p[0] + ox * r, p[1] + oy * r)
        arc = f'A{r:.2f},{r:.2f} 0 0 {1 if ix * oy - iy * ox > 0 else 0} {b[0]:.2f},{b[1]:.2f}'
        d += f' L{a[0]:.2f},{a[1]:.2f} {arc}'
        kerbs += f'M{a[0]:.2f},{a[1]:.2f} {arc}'
        segs += [(math.dist(cur, a), SPEED), (math.pi * r / 2, SPEED / 2)]
        cur = b
    segs.append((math.dist(cur, start), SPEED))

    out = f'<defs><path id="lap" d="{d} Z"/></defs>'
    out += f'<use href="#lap" fill="none" stroke="#f2f2f7" stroke-opacity=".55" stroke-width="{TRACK_W + .2}"/>'   # белые кромки
    out += (f'<path d="{kerbs}" fill="none" stroke="#f2f2f7" stroke-width="{TRACK_W + .2}"/>'   # поребрики в поворотах
            f'<path d="{kerbs}" fill="none" stroke="#ff3b30" stroke-width="{TRACK_W + .2}" stroke-dasharray=".16 .16"/>')
    out += f'<use href="#lap" fill="none" stroke="#2b2d33" stroke-width="{TRACK_W}"/>'
    sq = TRACK_W / 4   # клетчатая линия старт-финиш
    for row in range(4):
        for col in range(2):
            fill = '#f2f2f7' if (row + col) % 2 else '#0d0d0f'
            out += f'<rect x="{start[0] - sq + col * sq:.3f}" y="{start[1] - TRACK_W / 2 + row * sq:.3f}" width="{sq:.3f}" height="{sq:.3f}" fill="{fill}"/>'

    # скорость по участкам: доли пути (keyPoints) и доли времени круга (keyTimes)
    segs = [(length, v) for length, v in segs if length > 1e-6]
    total, lap = sum(length for length, _ in segs), sum(length / v for length, v in segs)
    points, times, a, t = ['0'], ['0'], 0, 0
    for length, v in segs:
        a, t = a + length, t + length / v
        points.append(f'{a / total:.4f}')
        times.append(f'{t / lap:.4f}')
    shadows, bodies = '', ''
    for i in range(len(CARS)):   # все едут одинаково, просто стартуют через равные доли круга
        motion = (f'<animateMotion dur="{lap:.2f}s" begin="-{lap * i / len(CARS):.2f}s" repeatCount="indefinite" '
                  f'rotate="auto" calcMode="linear" keyPoints="{";".join(points)}" keyTimes="{";".join(times)}">'
                  f'<mpath xlink:href="#lap"/></animateMotion>')
        shadows += f'<ellipse rx=".5" ry=".21" fill="#000" opacity=".45">{motion}</ellipse>'
        bodies += f'<use href="#car{i}">{motion}</use>'
    # корпус чуть приподнят над тенью: сдвиг (-l, -l) в сетке - это ровно вверх на экране
    return out + shadows + f'<g transform="translate(-.08 -.08)">{bodies}</g>'


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

    route = city_route(weeks, {(week, weekday) for _, week, weekday, count, _ in cells if count})
    on_track = set(route)

    # сначала вся земля, потом трасса с болидами, потом дома от дальних к ближним
    ground, houses = '', ''
    for _, week, weekday, count, n in sorted(cells):
        x = x0 + (week - weekday) * STEP_X
        y = y0 + (week + weekday) * STEP_Y
        if count == 0:
            kind = 'road' if (week, weekday) in on_track else ('lawn', 'walk')[int(random.Random(n).random() * 10) % 2]
            ground += f'<use href="#g-{kind}" x="{x:.1f}" y="{y:.1f}"/>'
            continue
        ground += f'<use href="#g-walk" x="{x:.1f}" y="{y:.1f}"/>'
        k = math.sqrt(count / best)   # корень, чтобы один большой день не съедал остальные
        floors = 1 + round(k * (MAX_FLOORS - 1))
        name = COMPOUNDS[min(int(k * len(COMPOUNDS)), len(COMPOUNDS) - 1)][0]
        top = y - floors * FLOOR_H
        houses += f'<use href="#b{floors}" x="{x:.1f}" y="{y:.1f}"/><use href="#r-{name}" x="{x:.1f}" y="{top:.1f}"/>'

    stars = ''
    rnd = random.Random(7)
    for _ in range(90):
        stars += f'<circle cx="{rnd.random() * W:.0f}" cy="{rnd.random() * 230:.0f}" r="{0.5 + rnd.random() * 0.9:.1f}" fill="#fff" opacity="{0.25 + rnd.random() * 0.6:.2f}"/>'

    legend = ''
    for i, (_, color, name) in enumerate(COMPOUNDS):
        x = W - 56 - 4 * 104 - 70 + i * 104
        legend += f'<rect x="{x - 9}" y="68" width="18" height="12" fill="{color}"/>'
        legend += f'<text x="{x + 18}" y="79" font-size="14" fill="#86868b">{name}</text>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last year as a night city: one building per day, more commits means more floors. Race cars lap a circuit that winds through the days without commits">
<defs>{make_defs()}</defs>
<g font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
<rect width="{W}" height="{H}" fill="#070a16"/>
{stars}
<ellipse cx="{W / 2}" cy="{y0 + 150}" rx="640" ry="270" fill="url(#glow)"/>
<text x="56" y="84" font-size="56" font-weight="700" letter-spacing="-2" fill="#f5f5f7">{total}</text>
<text x="56" y="116" font-size="18" font-weight="500" fill="#86868b">contributions · {first:%b %-d, %Y} – {last:%b %-d, %Y}</text>
{ground}
<g transform="matrix({STEP_X} {STEP_Y} {-STEP_X} {STEP_Y} {x0:.1f} {y0:.1f})">{race(circuit(weeks, route))}</g>
{houses}
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
