"""Validate public working tree and every tracked historical path before release."""
import json
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PREFIXES = ('data/raw/', 'library/', 'local_only/', 'private/')
FORBIDDEN_FILES = {'data/crossref_hits.jsonl', 'data/datacite_hits.json', 'data/supplemental_discovery.json', 'data/web_seed_records.json'}

def forbidden(name):
    return name.startswith(FORBIDDEN_PREFIXES) or name in FORBIDDEN_FILES or name.lower().endswith(('.pdf', '.bundle'))

def main():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT, text=True).split('\0')
    assert not [p for p in tracked if p and forbidden(p)], 'Local-only research files are tracked'
    history = subprocess.run(['git', 'rev-list', '--all', '--objects'], cwd=ROOT, text=True, capture_output=True)
    if history.returncode == 0:
        historical_paths = [s.split(' ', 1)[1] for s in history.stdout.splitlines() if ' ' in s]
        assert not [p for p in historical_paths if forbidden(p)], 'Historical raw/fulltext objects would become public'
    decisions = [json.loads(s) for s in (ROOT / 'data/processed/screening_decisions.jsonl').read_text(encoding='utf-8').splitlines()]
    records = [json.loads(s) for s in (ROOT / 'data/processed/corpus.jsonl').read_text(encoding='utf-8').splitlines()]
    assert all(not r.get('abstract') for r in decisions + records), 'Original abstract text in public JSONL'
    with sqlite3.connect(ROOT / 'data/processed/library.sqlite') as con:
        assert con.execute("SELECT COUNT(*) FROM records WHERE LENGTH(abstract)>0").fetchone()[0] == 0
    assert '\nAB  - ' not in (ROOT / 'data/processed/library.ris').read_text(encoding='utf-8')
    for name in ['academic_map.json']:
        a = json.loads((ROOT / 'data/processed' / name).read_text(encoding='utf-8'))
        assert all(not r.get('abstract') for r in a['records'])
    result = {'status': 'pass', 'public_records': len(records), 'public_original_abstracts': 0, 'tracked_pdfs': 0, 'historical_local_only_paths': 0, 'note': 'A distribution safeguard, not a legal clearance determination.'}
    (ROOT / 'data/processed/public_release_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
