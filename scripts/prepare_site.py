"""Copy only intentional private website assets to an existing Sites checkout."""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('site_checkout', type=Path)
args = parser.parse_args()
site = args.site_checkout.resolve()
manifest = site / '.openai/hosting.json'
assert manifest.exists(), 'Register and open the selected Site before packaging'
assert json.loads(manifest.read_text(encoding='utf-8'))['static']['directory'] == 'dist'
dist = site / 'dist'
dist.mkdir(exist_ok=True)
atlas = (ROOT / 'map.html').read_text(encoding='utf-8').replace('href="index.html" data-library', 'href="library.html" data-library')
(dist / 'index.html').write_text(atlas, encoding='utf-8')
(dist / 'map.html').write_text(atlas, encoding='utf-8')
shutil.copyfile(ROOT / 'index.html', dist / 'library.html')
paths = ['atlas.js', 'atlas.css', 'map-data.js', 'DISCLAIMER.md', 'RIGHTS.md']
paths += ['docs/' + p.name for p in (ROOT / 'docs').glob('*.md')]
paths += ['data/processed/' + name for name in ['library.ris', 'library.bib', 'library.sqlite', 'corpus.csv', 'core_cpi.csv', 'corpus.jsonl', 'research_extraction_template.csv', 'topic_cooccurrence.csv', 'citation_network.csv', 'academic_map.json', 'summary.json']]
for name in paths:
    target = dist / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / name, target)
# No raw retrieval cache, private source files, credentials, .git or browser
# profiles enter the web deployment. All attached exports inherit Site access.
print(json.dumps({'dist': str(dist), 'files': len(list(dist.rglob('*'))), 'bytes': sum(p.stat().st_size for p in dist.rglob('*') if p.is_file())}))
