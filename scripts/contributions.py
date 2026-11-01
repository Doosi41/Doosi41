#!/usr/bin/env python3
"""Выгружает всю историю коммитов (все годы) в docs/data/contributions.json.

Нужна интерактивной 3D-странице (docs/index.html) и картинке tires.py. Запускается в GitHub Actions.
Токен берётся из GITHUB_TOKEN, логин — из GH_LOGIN или владельца репозитория.
"""
import datetime as dt
import json
import os
import urllib.request

LOGIN = os.environ.get('GH_LOGIN') or os.environ.get('GITHUB_REPOSITORY_OWNER') or 'a1tvv'
TOKEN = os.environ['GITHUB_TOKEN']
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'data', 'contributions.json')

QUERY = '''query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    createdAt
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}'''


def graphql(variables):
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': variables}).encode(),
        headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get('errors'):
        raise SystemExit(data['errors'])
    return data['data']['user']


def main():
    now = dt.datetime.now(dt.timezone.utc)
    first = graphql({'login': LOGIN, 'from': now.isoformat(), 'to': now.isoformat()})
    start = dt.datetime.fromisoformat(first['createdAt'].replace('Z', '+00:00'))
    days = {}
    year = start.year
    while year <= now.year:  # API отдаёт максимум год за запрос
        frm = max(start, dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc))
        to = min(now, dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc))
        user = graphql({'login': LOGIN, 'from': frm.isoformat(), 'to': to.isoformat()})
        for week in user['contributionsCollection']['contributionCalendar']['weeks']:
            for day in week['contributionDays']:
                days[day['date']] = day['contributionCount']
        year += 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump({'login': LOGIN, 'generated': now.strftime('%Y-%m-%d'),
                   'days': [[d, c] for d, c in sorted(days.items())]}, f, separators=(',', ':'))
    print(f'{LOGIN}: {len(days)} days, {sum(days.values())} contributions')


if __name__ == '__main__':
    main()
