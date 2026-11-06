#!/usr/bin/env python3
"""Create a navigable local gallery from authentic saved test outputs."""
import argparse
import html
import json
from pathlib import Path
from urllib.parse import quote

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory', type=Path)
args = parser.parse_args()
root = args.directory.resolve()
rows = []
for file in sorted(root.glob('*/result.json')):
    result = json.loads(file.read_text())
    link = quote(file.parent.relative_to(root).as_posix()) + '/index.html'
    rows.append(f'<tr><td><a href="{link}">{html.escape(result["name"])}</a></td><td>{html.escape(result["status"])}</td><td>{html.escape(result["kind"])}</td></tr>')
images = []
for file in sorted(root.rglob('*.png')):
    relative = file.relative_to(root).as_posix()
    if 'attachments/' in relative or '/playwright-report/' in relative:
        continue  # These are exact attachments already present as named test captures.
    if file.name.startswith('report-'):
        kind = 'Captured test report'
    elif '/ui/' in relative or 'preview-browser/' in relative:
        kind = 'Browser design preview'
    elif file.name == 'blender-cpu-render.png':
        kind = 'Actual Blender CPU render in container'
    elif file.name == 'video-decoded-frame.png':
        kind = 'Actual decoded video test frame'
    elif any(marker in relative for marker in ['/native/', 'native-details/', 'desktop-details/', 'opengl-details/', 'capabilities-details/']):
        kind = 'Native desktop/application in container — software graphics'
    else:
        kind = 'Saved test image — consult its run metadata'
    images.append(f'<figure><figcaption>{html.escape(kind)} · {html.escape(relative)}</figcaption><a href="{quote(relative)}"><img src="{quote(relative)}" loading="lazy" alt="{html.escape(kind)}"></a></figure>')
document = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>OREZ test evidence</title><style>body{font:15px/1.6 system-ui;background:#f6f4ef;color:#222;max-width:1100px;margin:auto;padding:24px}h1{font-weight:500}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #ccc}a{color:inherit}img{max-width:100%;border:1px solid #ddd}figure{margin:35px 0}figcaption{overflow-wrap:anywhere;font-size:12px;margin-bottom:9px}</style><h1>OREZ / Test evidence</h1><p>Actual captures, including failed attempts. Browser previews and native applications in containers do not prove a booted or installable OS. Open a run for its command, source identity, result and full log.</p><table><tr><th>Run</th><th>Result</th><th>Environment</th></tr>'''
(root / 'index.html').write_text(document + ''.join(rows) + '</table><h2>Screenshots</h2>' + ''.join(images) + '</html>')
print(f'Gallery: {len(rows)} recorded runs; {len(images)} screenshot links')
