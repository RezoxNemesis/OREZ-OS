#!/usr/bin/env python3
"""Bundle every PNG capture for a run prefix, keeping exact duplicates once."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import zipfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path('dist/evidence'))
parser.add_argument('--prefix',required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
if args.output.exists(): raise SystemExit('Refusing to overwrite previous evidence')
folders=sorted(p for p in args.root.glob(args.prefix+'*') if p.is_dir())
images={}; references=[]; records=[]
for folder in folders:
 for path in sorted(folder.rglob('*.png')):
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  images.setdefault(digest,path)
  references.append({'source':str(path.relative_to(args.root)),'sha256':digest,'bytes':path.stat().st_size})
 for path in sorted(folder.glob('result.json')):
  value=json.loads(path.read_text());value['directory']=folder.name;records.append(value)
manifest={'scope':'All saved PNG files for the selected run prefix, including failed attempts.',
          'prefix':args.prefix,'unique_images':len(images),'capture_references':len(references),
          'references':references,'runs':records}
body=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OREZ daily-use evidence</title><style>body{font:16px/1.6 system-ui;max-width:1100px;margin:auto;padding:20px;background:#f6f4ef;color:#222}img{max-width:100%}figure{margin:32px 0}figcaption{overflow-wrap:anywhere}a{color:inherit}</style><h1>OREZ: actual test captures</h1><p>Includes failures. Report pages, browser previews and native container windows are distinct evidence. These do not establish an installed OS, physical compatibility or working Play Store. Consult manifest.json for every original path and result.</p>']
for record in records:
 body.append('<p>'+html.escape(record['directory']+': '+record['status']+' — '+record['name'])+'</p>')
for digest,path in images.items():
 source=str(path.relative_to(args.root))
 kind='Test report screenshot' if path.name.startswith('report-') else 'Native container capture' if 'native-details/' in source else 'Browser preview or captured test image — consult run metadata'
 body.append(f'<figure><figcaption>{html.escape(kind+": "+source)}</figcaption><a href="images/{digest}.png"><img loading="lazy" src="images/{digest}.png" alt="{html.escape(kind)}"></a></figure>')
body.append('</html>')
with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
 archive.writestr('index.html',''.join(body));archive.writestr('manifest.json',json.dumps(manifest,indent=2))
 for digest,path in images.items():archive.write(path,'images/'+digest+'.png')
 for folder in folders:
  for path in folder.iterdir():
   if path.is_file() and path.suffix in ['.json','.log','.txt']:
    archive.write(path,'records/'+str(path.relative_to(args.root)))
with zipfile.ZipFile(args.output) as archive:
 actual={hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('images/')}
 assert actual==set(images),'Screenshot hash-set mismatch'
summary={'path':str(args.output),'bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
         'unique_images':len(images),'capture_references':len(references),'runs':len(records)}
args.output.with_suffix('.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
