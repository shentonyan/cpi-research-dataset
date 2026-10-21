"""Offline deterministic screening, exports, SQLite, evidence ledger and browser."""
import csv
import hashlib
import html
import json
import re
import sqlite3
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from harvest import ROOT, CUTOFF

DATA = ROOT / 'data'
OUT = DATA / 'processed'
OUT.mkdir(exist_ok=True)

def norm(text):
    return re.sub(r'[^\w]+', ' ', unicodedata.normalize('NFKC', html.unescape(str(text))).lower()).strip()

def clean(text):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', str(text)))).strip()

def date_of(item):
    for field in ['published-online', 'published-print', 'published', 'issued']:
        parts = item.get(field, {}).get('date-parts', [[]])[0]
        if parts:
            return '-'.join(str(p).zfill(2 if i else 4) for i, p in enumerate(parts)), field
    return '', ''

def classify(title, abstract, streams):
    title, text = norm(title), norm(title + ' ' + abstract)
    if title.startswith('peer review report for'):
        return 'reference_context', 'B2_peer_review_report_not_a_research_article'
    cpi = 'cyber physical internet' in title
    logistics = re.search(r'logistic|transport|freight|shipment|router|routing|packet encapsulation|traceability|production|supply chain|asset service', text)
    if cpi and (logistics or 'towards cyber physical internet' in title):
        return 'core_cpi', 'I1_CPI_phrase_and_logistics_context'
    if cpi:
        return 'terminology_history', 'H1_CPI_name_without_logistics_context_manual_review_required'
    if 'physical internet' in title or 'internet physique' in title:
        return 'physical_internet', 'I2_PI_title'
    if 'cyber physical internet' in text and logistics:
        return 'cpi_context', 'I3_CPI_in_abstract_logistics_context'
    if re.search(r'hyperconnect|cyber physical|digital twin|interoperab', title) and re.search(r'logistic|supply chain|freight|transport|intralogistic', title):
        return 'enabling_research', 'I4_adjacent_logistics_technology_title'
    if 'seed_backward_reference' in streams:
        return 'reference_context', 'B1_cited_by_seed_not_directly_screened_as_CPI'
    return 'excluded', 'E1_no_topic_signal_in_available_title_abstract'

TAGS = {
 'routing': r'rout|path planning', 'incentives_pricing': r'auction|pricing|incentive|revenue|game theor|subscription',
 'architecture_protocols': r'architect|protocol|interoperab|reference model|tcp ip|address|framework',
 'capacity_congestion': r'capacity|bandwidth|congest|queue|throughput',
 'digital_twins_iot': r'digital twin|internet of things|\biot\b|cyber physical system',
 'sustainability_carbon': r'carbon|emission|sustainab|environment',
 'resilience_uncertainty': r'resilien|disrupt|uncertain|robust|stochastic',
 'learning_ai': r'learning|neural|artificial intelligence|\bllm\b|reasoning',
 'packing_containers': r'packing|encapsulation|container|modular',
 'privacy_security': r'privacy|security|blockchain|zero knowledge|trust',
 'cross_border': r'cross border|greater bay|\bgba\b',
 'manufacturing_intralogistics': r'manufactur|production|intralogistic|shop ?floor',
 'construction': r'construction|prefabricat',
 'review': r'review|survey|bibliometric',
}

def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(row.get(k), ensure_ascii=False) if isinstance(row.get(k), (list, dict)) else row.get(k, '') for k in fields})

def main():
    if not list((DATA / 'raw').glob('crossref_ranked_*.json')):
        raise SystemExit('Public release omits raw abstract caches. Run harvest.py/discover.py/enrich.py locally before rebuilding screening; see docs/public-release.md. Existing processed exports and maps can be used without reharvesting.')
    merged = {}
    def add(record, stream):
        doi = record.get('doi', '').lower().strip().removeprefix('https://doi.org/')
        key = 'doi:' + doi if doi else 'url:' + record.get('url', '')
        if not key.removeprefix('url:').strip():
            key = 'title:' + norm(record['title'])
        if key in merged:
            old = merged[key]
            old['streams'] = sorted(set(old.get('streams', []) + [stream]))
            old['discovery_urls'] = sorted(set(old.get('discovery_urls', []) + record.get('discovery_urls', []) + [record.get('url', '')]) - {''})
            # Complement missing metadata, preserving first-source values.
            for f in ['title', 'abstract', 'authors', 'year', 'journal', 'date', 'type', 'licenses', 'curator_tier', 'note_zh']:
                if not old.get(f) and record.get(f):
                    old[f] = record[f]
            return
        record.update(id=hashlib.sha256(key.encode()).hexdigest()[:16], doi=doi, streams=[stream], discovery_urls=record.get('discovery_urls', []) + [record.get('url', '')])
        merged[key] = record

    def crossref(item, stream):
        date, date_source = date_of(item)
        add({'title': clean(' '.join(item.get('title', []))), 'doi': item.get('DOI', ''), 'url': 'https://doi.org/' + item.get('DOI', ''), 'authors': [clean(a.get('given', '') + ' ' + a.get('family', a.get('name', ''))) for a in item.get('author', [])], 'date': date, 'date_source': date_source, 'year': int(date[:4]) if date else None, 'journal': clean(' '.join(item.get('container-title', []))), 'publisher': item.get('publisher', ''), 'type': item.get('type', ''), 'abstract': clean(item.get('abstract', '')), 'licenses': [v.get('URL', '') for v in item.get('license', [])], 'source': 'Crossref', 'metadata_status': 'registry_resolved', 'crossref_cited_by_snapshot': item.get('is-referenced-by-count'), 'relations': item.get('relation', {}), 'links': item.get('link', [])}, stream)

    # Read only final ranked search responses. Preserve the pilot files but do
    # not let their default index ordering contaminate the ranked retrieval log.
    for path in sorted((DATA / 'raw').glob('crossref_ranked_*.json')):
        payload = json.loads(path.read_text(encoding='utf-8'))
        for item in payload['response']['message'].get('items', []):
            crossref(item, path.stem.removeprefix('crossref_ranked_').rsplit('_', 1)[0])
    for path in sorted((DATA / 'raw').glob('doi_*.json')):
        payload = json.loads(path.read_text(encoding='utf-8'))
        crossref(payload['response']['message'], 'doi_resolution')
    # Preserve original provenance for backwards references when completed.
    hits = DATA / 'crossref_hits.jsonl'
    if hits.exists():
        for line in hits.read_text(encoding='utf-8').splitlines():
            r = json.loads(line)
            if r['stream'] in ['seed_backward_reference', 'verified_seed_doi']:
                crossref(r['record'], r['stream'])
    for p in (DATA / 'raw').glob('datacite_*.json'):
        raw = json.loads(p.read_text(encoding='utf-8'))
        for entry in raw['response'].get('data', []):
            a = entry['attributes']
            desc = ' '.join(x.get('description', '') for x in a.get('descriptions', []))
            add({'title': clean(' '.join(x.get('title', '') for x in a.get('titles', []))), 'doi': a.get('doi', ''), 'url': a.get('url') or 'https://doi.org/' + a['doi'], 'authors': [x.get('name', '') for x in a.get('creators', [])], 'year': a.get('publicationYear'), 'date': str(a.get('publicationYear', '')), 'type': a.get('types', {}).get('resourceTypeGeneral', ''), 'journal': '', 'abstract': clean(desc), 'source': 'DataCite', 'metadata_status': 'registry_resolved', 'licenses': [x.get('rightsUri', x.get('rights', '')) for x in a.get('rightsList', [])], 'relations': a.get('relatedIdentifiers', [])}, p.stem)
    for p in (DATA / 'raw').glob('hal_*.json'):
        raw = json.loads(p.read_text(encoding='utf-8'))
        for a in raw['response'].get('response', {}).get('docs', []):
            dois = a.get('doiId_s', [])
            if isinstance(dois, str):
                dois = [dois]
            add({'title': clean(' '.join(a.get('title_s', []))), 'doi': dois[0] if dois else '', 'url': a.get('uri_s', ''), 'authors': a.get('authFullName_s', []), 'year': a.get('producedDateY_i'), 'date': str(a.get('producedDateY_i', '')), 'type': a.get('docType_s', ''), 'journal': '', 'abstract': clean(' '.join(a.get('abstract_s', []))), 'source': 'HAL', 'metadata_status': 'repository_metadata', 'links': [{'URL': a.get('fileMain_s', '')}] if a.get('fileMain_s') else []}, p.stem)
    for p in (DATA / 'raw').glob('dblp_*.json'):
        raw = json.loads(p.read_text(encoding='utf-8'))
        for hit in raw['response'].get('result', {}).get('hits', {}).get('hit', []):
            a = hit['info']
            authors = a.get('authors', {}).get('author', [])
            if isinstance(authors, (str, dict)):
                authors = [authors]
            ee = a.get('ee', '')
            if isinstance(ee, list):
                ee = ee[0]
            add({'title': clean(a.get('title', '')), 'doi': a.get('doi', ''), 'url': ee or a.get('url', ''), 'authors': [x.get('text', '') if isinstance(x, dict) else x for x in authors], 'year': int(a['year']) if a.get('year') else None, 'date': a.get('year', ''), 'type': a.get('type', ''), 'journal': a.get('venue', ''), 'abstract': '', 'source': 'DBLP', 'metadata_status': 'index_metadata'}, p.stem)
    p = DATA / 'raw' / 'arxiv.xml'
    if p.exists():
        ns = {'a': 'http://www.w3.org/2005/Atom', 'ar': 'http://arxiv.org/schemas/atom'}
        for a in ET.fromstring(p.read_text(encoding='utf-8')).findall('a:entry', ns):
            value = lambda t: a.findtext(t, '', ns)
            add({'title': clean(value('a:title')), 'doi': value('ar:doi'), 'url': value('a:id').replace('http:', 'https:'), 'authors': [x.findtext('a:name', '', ns) for x in a.findall('a:author', ns)], 'year': int(value('a:published')[:4]), 'date': value('a:published')[:10], 'type': 'preprint', 'journal': value('ar:journal_ref'), 'abstract': clean(value('a:summary')), 'source': 'arXiv', 'metadata_status': 'repository_metadata'}, 'arxiv')
    for a in json.loads((DATA / 'curated_sources.json').read_text(encoding='utf-8')):
        a.update(abstract='', date=str(a.get('year') or ''), metadata_status='source_page_checked_partial_metadata', curator_tier=a['tier'])
        add(a, 'web_curated')

    fulltexts = json.loads((DATA / 'fulltext_manifest.json').read_text(encoding='utf-8')) if (DATA / 'fulltext_manifest.json').exists() else []
    ft = {x['doi']: x for x in fulltexts}
    records = []
    for a in merged.values():
        a['tier'], a['screening_reason'] = classify(a['title'], a.get('abstract', ''), a['streams'])
        if a.get('curator_tier'):
            a.update(tier=a['curator_tier'], screening_reason='M1_source_page_checked_curated_scope')
        if a.get('date', '') and a['date'] > CUTOFF and len(a['date']) >= 10:
            a.update(tier='excluded', screening_reason='E2_publication_after_cutoff')
        elif a.get('year') and int(a['year']) > int(CUTOFF[:4]):
            a.update(tier='excluded', screening_reason='E2_publication_after_cutoff')
        a['tags'] = [tag for tag, rx in TAGS.items() if re.search(rx, norm(a['title'] + ' ' + a.get('abstract', '')))]
        a['reading_status'] = 'not_read'
        a['review_status'] = 'peer_review_not_independently_verified'
        a['data_availability'] = 'not_assessed'
        a['code_availability'] = 'not_assessed'
        if a['doi'] in ['10.25442/hku.32593509', '10.25442/hku.32593509.v1']:
            a['data_availability'] = 'embargoed_files_public_metadata_only'
            a['note_zh'] = 'Figshare API：文件禁运，无可下载文件列表；仅收录公开元数据。概念 DOI 与版本 DOI 不计作独立数据。'
        a['license_scope'] = 'deposited_statements_not_a_fulltext_reuse_determination'
        a['fulltext_status'] = ft.get(a['doi'], {}).get('status', 'not_attempted')
        a['local_pdf'] = ft.get(a['doi'], {}).get('path', '')
        a['year'] = int(a['year']) if a.get('year') else None
        a['discovery_urls'] = sorted(set(x for x in a.get('discovery_urls', []) if x))
        a['source_abstract_available'] = bool(a.get('abstract'))
        a['abstract'] = ''
        a['abstract_release_policy'] = 'source_link_only_original_abstract_not_redistributed'
        records.append(a)
    records.sort(key=lambda a: (a['tier'] != 'core_cpi', -(a.get('year') or 0), norm(a['title']), a['id']))
    included = [a for a in records if a['tier'] != 'excluded']
    (OUT / 'corpus.jsonl').write_text(''.join(json.dumps(a, ensure_ascii=False) + '\n' for a in included), encoding='utf-8')
    (OUT / 'screening_decisions.jsonl').write_text(''.join(json.dumps(a, ensure_ascii=False) + '\n' for a in records), encoding='utf-8')
    fields = ['id', 'doi', 'title', 'authors', 'year', 'date', 'type', 'journal', 'tier', 'tags', 'url', 'abstract', 'source', 'streams', 'metadata_status', 'screening_reason', 'reading_status', 'review_status', 'fulltext_status', 'local_pdf', 'data_availability', 'code_availability', 'licenses', 'relations', 'discovery_urls', 'note_zh', 'source_abstract_available', 'abstract_release_policy']
    write_csv(OUT / 'corpus.csv', included, fields)
    write_csv(OUT / 'screening_decisions.csv', records, fields)
    write_csv(OUT / 'core_cpi.csv', [a for a in included if a['tier'] == 'core_cpi'], fields)
    export_bib(included)
    export_sqlite(included)
    groups = Counter(a['tier'] for a in included)
    summary = {'publication_cutoff': CUTOFF, 'built_on': '2026-10-22', 'unique_candidates': len(records), 'included_records': len(included), 'excluded_records': len(records) - len(included), 'tiers': dict(groups), 'with_abstract': sum(bool(a.get('abstract')) for a in included), 'with_doi': sum(bool(a['doi']) for a in included), 'archived_original_pdfs': sum(a.get('status') == 'archived_original' for a in fulltexts), 'core_with_abstract': sum(a['tier'] == 'core_cpi' and bool(a.get('abstract')) for a in included), 'core_records_are_not_unique_studies': True, 'core_critically_fulltext_reviewed': 0}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    create_reading_index(included, summary)
    create_browser(included, summary)
    # Title matches flag possible versions; never silently collapse different DOIs.
    titles = defaultdict(list)
    for a in included:
        titles[norm(a['title'])].append(a)
    (OUT / 'possible_versions.json').write_text(json.dumps([{'normalized_title': k, 'records': [{'id': a['id'], 'doi': a['doi'], 'url': a['url']} for a in v]} for k, v in titles.items() if len(v) > 1], ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))

def export_bib(records):
    bib, ris = [], []
    def esc(value):
        value = str(value)
        return value.replace('\\', '\\textbackslash{}').replace('{', '\\{').replace('}', '\\}').replace('&', '\\&').replace('%', '\\%').replace('_', '\\_').replace('#', '\\#')
    for a in records:
        if a['tier'] in ['projects_news', 'resource_portal']:
            continue
        kind = 'article' if a.get('type') == 'journal-article' else 'misc'
        fields = {'title': a['title'], 'author': ' and '.join(a.get('authors', [])), 'year': a.get('year') or '', 'journal': a.get('journal', ''), 'doi': a['doi'], 'url': a['url'], 'keywords': ', '.join(a['tags']), 'note': 'Scope: ' + a['tier'] + '; reading status: not critically reviewed'}
        bib.append('@' + kind + '{cpi' + a['id'] + ',\n' + ',\n'.join('  ' + k + ' = {' + esc(v) + '}' for k, v in fields.items() if v) + '\n}\n')
        lines = ['TY  - ' + ('JOUR' if kind == 'article' else 'GEN'), 'ID  - ' + a['id'], 'TI  - ' + a['title']]
        lines += ['AU  - ' + author for author in a.get('authors', [])]
        for tag, value in [('PY', a.get('year')), ('JO', a.get('journal')), ('DO', a['doi']), ('UR', a['url']), ('AB', a.get('abstract'))]:
            if value:
                lines.append(tag + '  - ' + str(value))
        lines.extend('KW  - ' + tag for tag in a['tags'])
        lines.extend(['N1  - Scope: ' + a['tier'] + '; fulltext review pending', 'ER  - '])
        ris.append('\n'.join(lines))
    (OUT / 'library.bib').write_text('\n'.join(bib), encoding='utf-8')
    (OUT / 'library.ris').write_text('\n\n'.join(ris), encoding='utf-8')

def export_sqlite(records):
    path = OUT / 'library.sqlite'
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as con:
        con.execute('CREATE TABLE records (id TEXT PRIMARY KEY, doi TEXT, title TEXT, authors TEXT, year INTEGER, tier TEXT, tags TEXT, abstract TEXT, url TEXT, reading_status TEXT, record_json TEXT)')
        con.execute('CREATE VIRTUAL TABLE search USING fts5(id UNINDEXED, title, authors, abstract, tags, tokenize="unicode61")')
        for a in records:
            author, tags = '; '.join(a.get('authors', [])), '; '.join(a['tags'])
            con.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?)', (a['id'], a['doi'], a['title'], author, a['year'], a['tier'], tags, a.get('abstract', ''), a['url'], a['reading_status'], json.dumps(a, ensure_ascii=False)))
            con.execute('INSERT INTO search VALUES (?,?,?,?,?)', (a['id'], a['title'], author, a.get('abstract', ''), tags))

def create_reading_index(records, summary):
    docs = ROOT / 'docs'
    docs.mkdir(exist_ok=True)
    lines = ['# CPI 核心文献索引', '', '此处为直接使用 CPI 术语且具有物流语境的文献记录，不是独立研究数量；预印本、会议版、期刊版与学位论文可能重叠。排序为年份倒序。所有精读状态初始为未精读。', '', '| 年份 | 文献 | 类型 | 摘要 | 本地全文 |', '|---|---|---|---|---|']
    for a in records:
        if a['tier'] == 'core_cpi':
            title = a['title'].replace('|', '\\|')
            pdf = '[PDF](../' + a['local_pdf'] + ')' if a['local_pdf'] else '未归档'
            lines.append(f"| {a['year'] or '待核'} | [{title}]({a['url']}) | {a.get('type', '')} | {'有' if a.get('abstract') else '待获取'} | {pdf} |")
    (docs / 'core-reading-index.zh-CN.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    matrix = []
    for a in records:
        if a['tier'] == 'core_cpi':
            matrix.append({**a, 'research_question': '', 'decision_variables': '', 'objective_constraints': '', 'method': '', 'data_origin': '', 'baselines': '', 'identification_or_proof': '', 'limitations': '', 'replication_status': 'not_started', 'evidence_locator': ''})
    write_csv(OUT / 'research_extraction_template.csv', matrix, ['id', 'doi', 'title', 'year', 'research_question', 'decision_variables', 'objective_constraints', 'method', 'data_origin', 'baselines', 'identification_or_proof', 'limitations', 'replication_status', 'evidence_locator'])

def create_browser(records, summary):
    template = (ROOT / 'scripts' / 'browser.html').read_text(encoding='utf-8')
    payload = json.dumps({'records': records, 'summary': summary}, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    (ROOT / 'index.html').write_text(template.replace('__DATA_JSON__', payload), encoding='utf-8')

if __name__ == '__main__':
    main()
