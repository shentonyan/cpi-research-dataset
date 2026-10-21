"""Build an auditable academic map from the retained corpus; no API calls."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed'
LABELS = {
 'routing': ('路由与路径', 'Routing', 'decision'),
 'incentives_pricing': ('激励与定价', 'Incentives', 'decision'),
 'architecture_protocols': ('架构与协议', 'Architecture', 'infrastructure'),
 'capacity_congestion': ('能力与拥堵', 'Capacity', 'decision'),
 'digital_twins_iot': ('数字孪生与物联网', 'Digital twins / IoT', 'infrastructure'),
 'sustainability_carbon': ('可持续与碳排放', 'Sustainability', 'outcomes'),
 'resilience_uncertainty': ('韧性与不确定性', 'Resilience', 'outcomes'),
 'learning_ai': ('学习与人工智能', 'Learning / AI', 'decision'),
 'packing_containers': ('封装与集装单元', 'Encapsulation', 'infrastructure'),
 'privacy_security': ('隐私与安全', 'Privacy', 'outcomes'),
 'cross_border': ('跨境物流', 'Cross-border', 'applications'),
 'manufacturing_intralogistics': ('制造与内部物流', 'Manufacturing', 'applications'),
 'construction': ('建造物流', 'Construction', 'applications'),
 'review': ('综述与研究框架', 'Reviews', 'infrastructure'),
}
SCOPES = {'core': {'core_cpi', 'cpi_context'}, 'broad': {'core_cpi', 'cpi_context', 'physical_internet', 'enabling_research'}}

def layout(graph, iterations=150):
    if not len(graph):
        return {}
    positions = nx.spring_layout(graph, seed=20261022, weight='weight', iterations=iterations)
    return {key: [round(float(v[0]), 5), round(float(v[1]), 5)] for key, v in positions.items()}

def main():
    records = [json.loads(s) for s in (DATA / 'corpus.jsonl').read_text(encoding='utf-8').splitlines()]
    bydoi = {r['doi']: r for r in records if r['doi']}
    themes = {}
    for scope, tiers in SCOPES.items():
        subset = [r for r in records if r['tier'] in tiers]
        membership = {tag: [r['id'] for r in subset if tag in r['tags']] for tag in LABELS}
        counts = Counter(tuple(sorted(pair)) for r in subset for pair in itertools.combinations(sorted(set(r['tags']) & LABELS.keys()), 2))
        graph = nx.Graph()
        graph.add_nodes_from(LABELS)
        graph.add_weighted_edges_from((a, b, count) for (a, b), count in counts.items())
        # Fixed circular topic layout keeps labels legible in a dense graph.
        # Position carries no semantic or importance interpretation.
        import math
        coords = {tag: [round(math.cos(-math.pi / 2 + 2 * math.pi * i / len(LABELS)), 5), round(math.sin(-math.pi / 2 + 2 * math.pi * i / len(LABELS)), 5)] for i, tag in enumerate(LABELS)}
        themes[scope] = {'record_count': len(subset), 'nodes': [{'id': tag, 'label': names[0], 'en': names[1], 'group': names[2], 'count': len(membership[tag]), 'papers': membership[tag], 'position': coords[tag]} for tag, names in LABELS.items()], 'edges': [{'source': a, 'target': b, 'weight': weight} for (a, b), weight in sorted(counts.items())]}
    raw = [json.loads(s) for s in (ROOT / 'data/citation_edges.jsonl').read_text(encoding='utf-8').splitlines()]
    edges = sorted({(bydoi[e['source_doi']]['id'], bydoi[e['target_doi']]['id']) for e in raw if e['source_doi'] in bydoi and e['target_doi'] in bydoi and e['source_doi'] != e['target_doi']})
    graph = nx.Graph()
    graph.add_edges_from(edges)
    graph.add_nodes_from(r['id'] for r in records if r['tier'] == 'core_cpi')
    coordinates = layout(graph, 220)
    byid = {r['id']: r for r in records}
    citations = {'nodes': [{'id': key, 'position': coordinates[key], 'degree': graph.degree(key), 'core': byid[key]['tier'] == 'core_cpi'} for key in sorted(graph)], 'edges': [{'source': a, 'target': b} for a, b in edges], 'raw_reference_rows': len(raw), 'resolved_reference_rows': sum(e['source_doi'] in bydoi and e['target_doi'] in bydoi for e in raw), 'unique_sources': len({a for a, _ in edges}), 'unresolved_or_outside_corpus_rows': sum(e['source_doi'] not in bydoi or e['target_doi'] not in bydoi for e in raw)}
    corpus_hash = hashlib.sha256((DATA / 'corpus.jsonl').read_bytes()).hexdigest()
    payload = {'version': 1, 'built_on': '2026-10-22', 'publication_cutoff': '2026-10-21', 'layout_seed': 20261022, 'corpus_sha256': corpus_hash, 'records': records, 'themes': themes, 'citations': citations, 'yearly': [{'year': y, 'core': sum(r['year'] == y and r['tier'] == 'core_cpi' for r in records), 'narrow': sum(r['year'] == y and r['tier'] in SCOPES['core'] for r in records), 'broad': sum(r['year'] == y and r['tier'] in SCOPES['broad'] for r in records)} for y in sorted({r['year'] for r in records if r['year'] and r['tier'] in SCOPES['broad']})]}
    (DATA / 'academic_map.json').write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    js = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e')
    (ROOT / 'map-data.js').write_text('window.CPI_MAP_DATA=' + js + ';\n', encoding='utf-8')
    # Long-form edges can be independently recomputed, without the visualization.
    import csv
    with (DATA / 'topic_cooccurrence.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['scope', 'source_theme', 'target_theme', 'record_cooccurrence_count'])
        for scope, data in themes.items():
            w.writerows([scope, e['source'], e['target'], e['weight']] for e in data['edges'])
    with (DATA / 'citation_network.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['citing_id', 'citing_doi', 'cited_id', 'cited_doi'])
        w.writerows([a, byid[a]['doi'], b, byid[b]['doi']] for a, b in edges)
    print(json.dumps({'theme_scopes': {k: v['record_count'] for k, v in themes.items()}, 'citation_nodes': len(citations['nodes']), 'unique_directed_citation_edges': len(edges), 'citing_seeds': citations['unique_sources']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
