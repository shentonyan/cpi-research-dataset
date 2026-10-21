"""Add web-discovered DOI seeds and archive explicitly licensed originals."""
import concurrent.futures as cf
import hashlib
import json
import re
from pathlib import Path

import pymupdf
import requests

from harvest import ROOT, fetch_doi

DOIS = [
 '10.1016/j.aei.2024.102551', '10.1016/j.eswa.2024.126003',
 '10.1016/j.tre.2026.104843', '10.1016/j.cie.2026.112232',
 '10.1109/JIOT.2025.3562803', '10.1109/TITS.2025.3581569',
 '10.1108/IJRDM-01-2025-0042', '10.1109/CASE59546.2024.10711556',
 '10.1016/j.jii.2025.100935', '10.1016/j.tre.2026.104915',
 '10.1016/j.trc.2024.104714', '10.1016/j.trd.2024.104259',
 '10.1109/ICNSC66229.2025.00056', '10.1016/j.aei.2025.103830',
 '10.1080/13675567.2026.2655353', '10.1109/CASE69030.2026.11704537',
 '10.1109/CASE59546.2024.10711404', '10.2139/ssrn.4891853',
 '10.1016/j.tre.2024.103842',
]
PDFS = [
 ('10.1016/j.tre.2025.104051', 'https://ira.lib.polyu.edu.hk/bitstream/10397/111680/1/1-s2.0-S1366554525000924-main.pdf'),
 ('10.1016/j.ifacol.2023.10.1160', 'https://ira.lib.polyu.edu.hk/bitstream/10397/110365/1/1-s2.0-S240589632301563X-main.pdf'),
 ('10.21494/ISTE.OP.2019.0422', 'https://www.openscience.fr/IMG/pdf/iste_induprod19v2n1_5.pdf'),
 ('10.1080/13675567.2026.2658585', 'https://www.tandfonline.com/doi/pdf/10.1080/13675567.2026.2658585'),
]

def archive(spec):
    doi, url = spec
    out = {'doi': doi.lower(), 'url': url, 'retrieved_date': '2026-10-22'}
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        if not r.content.startswith(b'%PDF'):
            raise ValueError('Response was not a PDF')
        doc = pymupdf.open(stream=r.content, filetype='pdf')
        text = '\n'.join(p.get_text() for p in doc)
        # Require an explicit CC statement inside the PDF. Mere accessibility
        # or a publisher landing-page license link is not a redistribution grant.
        cc = re.search(r'https?://creativecommons\.org/licenses/[a-z\-/\d.]+', text, re.I)
        if not cc:
            out.update(status='link_only_license_not_confirmed', pages=len(doc))
            return out
        filename = hashlib.sha256(doi.lower().encode()).hexdigest()[:12] + '.pdf'
        path = ROOT / 'library' / 'pdf' / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
        out.update(status='archived_original', path=str(path.relative_to(ROOT)).replace('\\', '/'), sha256=hashlib.sha256(r.content).hexdigest(), bytes=len(r.content), pages=len(doc), license_url=cc.group(0).rstrip(').'), reading_status='machine_text_extracted_not_fulltext_reviewed')
        # Extraction stays private, text is used to find candidates only, not
        # as evidence that an article has been critically read.
        (ROOT / 'library' / 'text').mkdir(exist_ok=True)
        (ROOT / 'library' / 'text' / filename.replace('.pdf', '.txt')).write_text(text, encoding='utf-8')
    except Exception as exc:
        out.update(status='fetch_failed', error=str(exc))
    return out

def main():
    records, logs = [], []
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for record, log in pool.map(fetch_doi, DOIS):
            logs.append(log)
            if record:
                records.append(record)
    (ROOT / 'data' / 'web_seed_records.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'data' / 'web_seed_resolution_log.json').write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding='utf-8')
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        pdfs = list(pool.map(archive, PDFS))
    (ROOT / 'data' / 'fulltext_manifest.json').write_text(json.dumps(pdfs, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'resolved_web_seeds': len(records), 'fulltext': pdfs}, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
