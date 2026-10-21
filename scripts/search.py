"""Usage: python scripts/search.py 'routing AND carbon' --tier core_cpi"""
import argparse
import sqlite3
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('query', help='SQLite FTS5 query; quote multiword phrases')
parser.add_argument('--tier')
parser.add_argument('--limit', type=int, default=20)
args = parser.parse_args()
path = Path(__file__).resolve().parents[1] / 'data/processed/library.sqlite'
with sqlite3.connect(path) as con:
    sql = 'SELECT r.year, r.tier, r.title, r.url FROM search s JOIN records r ON s.id=r.id WHERE search MATCH ?'
    params = [args.query]
    if args.tier:
        sql += ' AND r.tier=?'
        params.append(args.tier)
    sql += ' ORDER BY rank LIMIT ?'
    params.append(max(1, min(args.limit, 1000)))
    try:
        rows = con.execute(sql, params).fetchall()
    except sqlite3.OperationalError as exc:
        parser.error(str(exc))
    for year, tier, title, url in rows:
        print(f'[{year or "?"}] [{tier}] {title}\n{url}\n')
    print(f'{len(rows)} result(s)')
