"""Package Git-tracked release files only; ignored PDFs/caches cannot enter."""
import argparse
import subprocess
import zipfile
from pathlib import Path
from validate_public import forbidden, main as validate

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
validate()
paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root, text=True).split('\0')
with zipfile.ZipFile(args.output.resolve(), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for rel in paths:
        if rel and not forbidden(rel):
            archive.write(root / rel, 'cpi-research-dataset/' + rel)
with zipfile.ZipFile(args.output) as archive:
    assert archive.testzip() is None
print(str(args.output.resolve()))
