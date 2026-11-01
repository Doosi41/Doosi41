"""Чёрная версия profile-gitblock.svg: тот же рисунок, но фон чёрный, текст светлый, пустые клетки тёмные.
Запускается в Action после github-profile-3d-contrib (он каждый раз пересоздаёт светлую версию)."""
import re

SRC = 'profile-3d-contrib/profile-gitblock.svg'
DST = 'profile-3d-contrib/profile-gitblock-black.svg'

svg = open(SRC, encoding='utf-8').read()
for old, new in [
    ('.fill-fg { fill: #00000f; }', '.fill-fg { fill: #f5f5f7; }'),
    ('.stroke-fg { stroke: #00000f; }', '.stroke-fg { stroke: #f5f5f7; }'),
    ('.fill-bg { fill: #ffffff; }', '.fill-bg { fill: #000000; }'),
    ('.stroke-bg { stroke: #ffffff; }', '.stroke-bg { stroke: #000000; }'),
    ('.fill-strong { fill: #111133; }', '.fill-strong { fill: #ffffff; }'),
    ('.cont-top-bg-0 { fill: #f8f8f8; }', '.cont-top-bg-0 { fill: #4a4a4e; }'),
    ('.cont-top-fg-0 { fill: #aaaaaa; }', '.cont-top-fg-0 { fill: #6a6a70; }'),
    ('.cont-right-bg-0 { fill: rgb(174, 174, 174); }', '.cont-right-bg-0 { fill: #36363a; }'),
    ('.cont-right-fg-0 { fill: rgb(119, 119, 119); }', '.cont-right-fg-0 { fill: #505055; }'),
    ('.cont-left-bg-0 { fill: rgb(207, 207, 207); }', '.cont-left-bg-0 { fill: #414145; }'),
    ('.cont-left-fg-0 { fill: rgb(142, 142, 142); }', '.cont-left-fg-0 { fill: #5e5e63; }'),
]:
    assert old in svg, old
    svg = svg.replace(old, new)
open(DST, 'w', encoding='utf-8').write(svg)
