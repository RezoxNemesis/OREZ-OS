#!/usr/bin/env python3
"""Read-only integrity check for a Docker save archive before deleting QA caches."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive',type=Path)
parser.add_argument('--required-tag',action='append',default=[])
args=parser.parse_args()
manifest=None; verified={}
with tarfile.open(args.archive,'r|gz') as archive:
 for entry in archive:
  if not entry.isfile():continue
  stream=archive.extractfile(entry)
  if entry.name=='manifest.json':manifest=json.load(stream)
  elif entry.name.startswith('blobs/sha256/'):
   expected=entry.name.rsplit('/',1)[1];digest=hashlib.sha256()
   while chunk:=stream.read(1024*1024):digest.update(chunk)
   if digest.hexdigest()!=expected:raise SystemExit('Backup blob checksum mismatch: '+entry.name)
   verified[entry.name]=entry.size
if not manifest:raise SystemExit('Docker save manifest missing')
tags={tag for image in manifest for tag in (image.get('RepoTags') or [])}
if not set(args.required_tag)<=tags:raise SystemExit('Required saved image tag missing')
for image in manifest:
 for name in [image['Config'],*image['Layers']]:
  if name not in verified:raise SystemExit('Unverified referenced backup blob: '+name)
print(json.dumps({'status':'PASS','archive':str(args.archive),'compressed_bytes':args.archive.stat().st_size,
 'verified_blobs':len(verified),'tags':sorted(tags),'scope':'QA dependency-image backup, not OS installation or recovery'},indent=2))
