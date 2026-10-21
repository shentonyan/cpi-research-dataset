"""Independently reconcile map output against corpus and raw references."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = ROOT / 'data/processed'
payload = json.loads((data / 'academic_map.json').read_text(encoding='utf-8'))
records = [json.loads(s) for s in (data / 'corpus.jsonl').read_text(encoding='utf-8').splitlines()]
assert payload['corpus_sha256'] == hashlib.sha256((data / 'corpus.jsonl').read_bytes()).hexdigest()
byid = {r['id']: r for r in records}
bydoi = {r['doi']: r['id'] for r in records if r['doi']}
for name, tiers in [('core', ['core_cpi', 'cpi_context']), ('broad', ['core_cpi', 'cpi_context', 'physical_internet', 'enabling_research'])]:
    subset = [r for r in records if r['tier'] in tiers]
    graph = payload['themes'][name]
    assert graph['record_count'] == len(subset)
    allowed = {n['id'] for n in graph['nodes']}
    counts = Counter(tuple(sorted(pair)) for r in subset for pair in itertools.combinations(set(r['tags']) & allowed, 2))
    assert {(e['source'], e['target']): e['weight'] for e in graph['edges']} == dict(counts)
    for n in graph['nodes']:
        expected = {r['id'] for r in subset if n['id'] in r['tags']}
        assert set(n['papers']) == expected and n['count'] == len(expected)
raw = [json.loads(s) for s in (ROOT / 'data/citation_edges.jsonl').read_text(encoding='utf-8').splitlines()]
expected = {(bydoi[e['source_doi']], bydoi[e['target_doi']]) for e in raw if e['source_doi'] in bydoi and e['target_doi'] in bydoi and e['source_doi'] != e['target_doi']}
actual = {(e['source'], e['target']) for e in payload['citations']['edges']}
assert expected == actual
nodeids = {n['id'] for n in payload['citations']['nodes']}
assert all(a in nodeids and b in nodeids for a, b in actual)
assert all(r['id'] in nodeids for r in records if r['tier'] == 'core_cpi')
for row in payload['yearly']:
    assert row['core'] == sum(r['year'] == row['year'] and r['tier'] == 'core_cpi' for r in records)
    assert row['narrow'] == sum(r['year'] == row['year'] and r['tier'] in ['core_cpi', 'cpi_context'] for r in records)
result = {'status': 'pass', 'checks': ['corpus checksum', 'topic membership and all cooccurrence weights', 'citation directions and deduplication against raw references', 'node endpoint coverage', 'core isolated-node retention', 'year and scope reconciliation'], 'citation_nodes': len(nodeids), 'citation_edges': len(actual)}
(data / 'academic_map_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
