"""Complement Crossref with HAL, DBLP and arXiv; preserve access failures."""
import concurrent.futures as cf
import json
import xml.etree.ElementTree as ET
import requests
from harvest import ROOT, get_json

def main():
    specs = [
        ('hal_cpi', 'https://api.archives-ouvertes.fr/search/', {'q': '"cyber-physical internet"', 'rows': 500, 'fl': 'halId_s,title_s,authFullName_s,producedDateY_i,doiId_s,uri_s,docType_s,abstract_s,fileMain_s', 'wt': 'json'}),
        ('hal_pi', 'https://api.archives-ouvertes.fr/search/', {'q': 'title_t:"physical internet"', 'rows': 1000, 'fl': 'halId_s,title_s,authFullName_s,producedDateY_i,doiId_s,uri_s,docType_s,abstract_s,fileMain_s', 'wt': 'json'}),
        ('dblp_cpi', 'https://dblp.org/search/publ/api', {'q': 'cyber physical internet', 'format': 'json', 'h': 1000}),
        ('dblp_pi', 'https://dblp.org/search/publ/api', {'q': 'physical internet', 'format': 'json', 'h': 1000}),
    ]
    def run(spec):
        name, url, params = spec
        payload = get_json(url, params, name + '.json')
        print(name, 'error' if 'error' in payload else 'ok', flush=True)
        return name, payload
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        data = dict(pool.map(run, specs))
    try:
        url = 'https://export.arxiv.org/api/query'
        params = {'search_query': 'ti:"physical internet" OR ti:"cyber-physical internet"', 'max_results': 300, 'sortBy': 'submittedDate', 'sortOrder': 'descending'}
        p = ROOT / 'data' / 'raw' / 'arxiv.xml'
        if not p.exists():
            response = requests.get(url, params=params, timeout=50)
            response.raise_for_status()
            ET.fromstring(response.text)
            p.write_text(response.text, encoding='utf-8')
        data['arxiv'] = {'status': 'ok', 'raw': 'data/raw/arxiv.xml', 'query': params}
    except Exception as exc:
        data['arxiv'] = {'error': str(exc)}
    (ROOT / 'data' / 'supplemental_discovery.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('supplemental discovery complete', flush=True)

if __name__ == '__main__':
    main()
