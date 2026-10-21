"""Auditable, resumable Crossref + DataCite discovery. No credentials required.

Search relevance is NOT inclusion; all downloaded hits are retained with decisions.
Run from repository root. Cached API responses are immutable on subsequent runs.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data' / 'raw'
CACHE.mkdir(parents=True, exist_ok=True)
CUTOFF = '2026-10-21'
STREAMS = [
    ('cpi_title', 'Cyber-Physical Internet', 'query.title', 2, 500),
    ('cpi_all', '"cyber-physical internet"', 'query', 2, 500),
    ('pi_title', 'Physical Internet', 'query.title', 4, 500),
    ('cpl_title', 'Cyber physical logistics', 'query.title', 1, 300),
    ('dt_pi', 'digital twins physical internet', 'query', 1, 300),
    ('hyperconnected', 'hyperconnected logistics', 'query.title', 1, 300),
    ('cpi_chinese', '元联网', 'query', 1, 200),
]
SEEDS = [
    '10.1016/j.tre.2025.104051', '10.1016/j.cie.2024.110293',
    '10.1016/j.ifacol.2023.10.1160', '10.1080/13675567.2026.2658585',
    '10.2139/ssrn.5180628', '10.21494/ISTE.OP.2019.0422',
    '10.1002/9781119987420.ch12', '10.1016/j.cie.2019.106170',
    '10.1007/s10845-023-02262-6', '10.1016/j.dte.2024.100025',
]

def get_json(url, params=None, cache_name=None):
    path = CACHE / (cache_name or (hashlib.sha256((url + json.dumps(params, sort_keys=True)).encode()).hexdigest() + '.json'))
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    error = None
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, timeout=75, headers={'User-Agent': 'CPIResearchDataset/0.1 (private scholarly bibliography)'})
            r.raise_for_status()
            payload = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'url': r.url, 'response': r.json()}
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            return payload
        except Exception as exc:
            error = str(exc)
            time.sleep(2 ** attempt)
    return {'error': error, 'url': url, 'params': params}

def stream(spec):
    name, query, field, pages, rows = spec
    cursor = '*'
    logs, works = [], []
    for page in range(pages):
        payload = get_json('https://api.crossref.org/works', {field: query, 'rows': rows, 'cursor': cursor, 'sort': 'score', 'order': 'desc', 'filter': f'until-pub-date:{CUTOFF}'}, f'crossref_ranked_{name}_{page:02}.json')
        if 'error' in payload:
            logs.append({'stream': name, 'query': query, 'error': payload['error']})
            break
        msg = payload['response']['message']
        items = msg.get('items', [])
        works.extend((item, name) for item in items)
        logs.append({'stream': name, 'query': query, 'field': field, 'page': page + 1, 'returned': len(items), 'reported_total_fuzzy_hits': msg.get('total-results'), 'retrieved_at': payload['retrieved_at'], 'request_url': payload['url'], 'cache': f'data/raw/crossref_ranked_{name}_{page:02}.json'})
        cursor = msg.get('next-cursor')
        if not cursor or len(items) < rows:
            break
        time.sleep(.5)
    print(name, len(works), flush=True)
    return works, logs

def fetch_doi(doi):
    payload = get_json('https://api.crossref.org/works/' + quote(doi, safe=''), cache_name='doi_' + hashlib.sha256(doi.lower().encode()).hexdigest()[:16] + '.json')
    if 'error' in payload:
        return None, {'doi': doi, 'error': payload['error']}
    return payload['response']['message'], {'doi': doi, 'retrieved_at': payload['retrieved_at'], 'request_url': payload['url']}

def main():
    allworks, logs, errors = [], [], []
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for works, log in pool.map(stream, STREAMS):
            allworks.extend(works)
            logs.extend(log)
    seeds = []
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for item, log in pool.map(fetch_doi, SEEDS):
            if item:
                seeds.append(item)
                allworks.append((item, 'verified_seed_doi'))
            else:
                errors.append(log)
    # One-hop backwards citation expansion; keep every reference edge, even when
    # the target is not relevant or has no DOI. Resolve unique DOI targets only.
    edges, refdois = [], set()
    for seed in seeds:
        for ref in seed.get('reference', []):
            doi = ref.get('DOI', '').lower().strip()
            if doi:
                refdois.add(doi)
            edges.append({'source_doi': seed['DOI'].lower(), 'target_doi': doi, 'reference': ref})
    known = {w.get('DOI', '').lower() for w, _ in allworks}
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for item, log in pool.map(fetch_doi, sorted(refdois - known)):
            if item:
                allworks.append((item, 'seed_backward_reference'))
            else:
                errors.append(log)
    datacite = []
    for name, query in [('cpi', '"cyber-physical internet"'), ('pi', 'titles.title:"physical internet"')]:
        payload = get_json('https://api.datacite.org/dois', {'query': query, 'page[size]': 1000}, f'datacite_{name}.json')
        if 'error' in payload:
            errors.append(payload)
        else:
            datacite.extend(payload['response'].get('data', []))
            logs.append({'stream': 'datacite_' + name, 'query': query, 'returned': len(payload['response'].get('data', [])), 'reported_total': payload['response'].get('meta', {}).get('total'), 'request_url': payload['url'], 'retrieved_at': payload['retrieved_at'], 'cache': f'data/raw/datacite_{name}.json'})
    out = ROOT / 'data'
    (out / 'crossref_hits.jsonl').write_text(''.join(json.dumps({'stream': s, 'record': w}, ensure_ascii=False) + '\n' for w, s in allworks), encoding='utf-8')
    (out / 'datacite_hits.json').write_text(json.dumps(datacite, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'citation_edges.jsonl').write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in edges), encoding='utf-8')
    (out / 'search_log.json').write_text(json.dumps({'cutoff': CUTOFF, 'streams': logs, 'errors': errors, 'notes': ['Crossref search is relevance-ranked, not Boolean exact matching.', 'Page caps are deliberate and must be disclosed.', 'DataCite search may match descriptions; titles are screened afterwards.', 'No OpenAlex key was available: OpenAlex was not queried.', 'No Scopus/WoS/CNKI subscription search was performed.']}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'crossref_hits_with_duplicates': len(allworks), 'backward_edges': len(edges), 'datacite_hits': len(datacite), 'errors': len(errors)}), flush=True)

if __name__ == '__main__':
    main()
