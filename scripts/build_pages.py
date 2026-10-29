#!/usr/bin/env python3
"""Generate the website demo directly from the current OpenFIDS app and database."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'demo'

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    ui = (ROOT / 'app' / 'index.html').read_text(encoding='utf-8')
    marker = '<script>\n(() => {'
    assert ui.count(marker) == 1, 'Cannot find OpenFIDS boot script'
    ui = ui.replace(marker, '<script src="./shim.js"></script>\n' + marker, 1)
    ui = ui.replace("const LS = 'openfids.v2';", "const LS = 'openfids.demo.v1';")
    ui = ui.replace('<title>OpenFIDS</title>', '<title>OpenFIDS · Live preview</title>', 1)
    (OUT / 'index.html').write_text(
        '<!-- Generated from app/index.html. See scripts/build_pages.py. -->\n'+ui, encoding='utf-8')
    db = runpy.run_path(str(ROOT / 'app' / 'database.py'))
    (OUT / 'database.json').write_text(
        json.dumps({'aircraft':db['AIRCRAFT_DB'],'airlines':db['AIRLINE_DB']},
                   ensure_ascii=False,sort_keys=True,separators=(',',':')),encoding='utf-8')

if __name__ == '__main__':
    build()
