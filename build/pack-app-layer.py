#!/usr/bin/env python3
"""Pack and independently extract a local, audited app delta; NOT a release ISO.

Inputs are outputs of this repository's trusted local build, not untrusted
download manifests. The caller must authenticate the upstream ISO separately.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from app_layer import delta, inventory
from image_packages import sha

spec=importlib.util.spec_from_file_location('stage_image_root',Path(__file__).with_name('stage-image-root.py'))
staging=importlib.util.module_from_spec(spec);spec.loader.exec_module(staging)


def pseudo_xattrs(lines):
    """Read unsquashfs 4.x pseudo metadata; refuse ambiguous escaped paths."""
    result={}
    for line in lines:
        if ' x ' not in line:continue
        path,value=line.rstrip('\n').split(' x ',1)
        parsed=PurePosixPath(path)
        if '\\' in path or '"' in path or parsed.is_absolute() or '..' in parsed.parts or str(parsed)!=path:
            raise ValueError('Extended attribute path needs explicit review')
        if not value or '=' not in value:raise ValueError('Malformed extended attribute record')
        result.setdefault(path,[]).append(value)
    return result


def original_xattrs(iso,offset):
    # Stop at the documented pseudo data marker: never copy 11 GB of file data.
    # This metadata is read directly from the hash-bound original image.
    with tempfile.TemporaryFile() as errors:
        p=subprocess.Popen(['unsquashfs','-no-progress','-o',str(offset),'-pf','-',str(iso)],
                           stdout=subprocess.PIPE,stderr=errors)
        lines=[];size=0;complete=False
        try:
            for line in p.stdout:
                size+=len(line)
                if size>80*1024**2:raise ValueError('Original metadata exceeds reviewed limit')
                if line.startswith(b'# START OF DATA'):
                    complete=True;break
                lines.append(line.decode('utf-8',errors='strict'))
        finally:
            p.terminate();p.wait(timeout=10);p.stdout.close()
        if not complete:raise ValueError('Incomplete original metadata; do not assume no xattrs')
    return pseudo_xattrs(lines)


def expected_layer(before,after):
    changed=delta(before,after);paths=set(changed)
    for path in changed:paths.update(str(p) for p in PurePosixPath(path).parents if str(p)!='.')
    return {path:after[path] for path in paths}


def pack(args):
    os.umask(0o022);staging.require_build_container()
    installed=staging.work_path(args.installed);output=staging.work_path(args.output)
    if args.epoch<0 or args.epoch>2**32-1:raise ValueError('Invalid fixed build timestamp')
    marker=json.loads(args.marker.read_text());report=json.loads((installed/'report.json').read_text())
    if (marker.get('purpose')!='orez-additive-package-staging' or
        marker.get('input_iso_sha256')!=report['source_iso_sha256'] or
        report.get('installation_approved') is not False or
        marker['input_iso_sha256']!=sha(args.iso)):
        raise ValueError('Original image identity/report mismatch')
    before=json.loads((installed/'before.json').read_text());after=json.loads((installed/'after.json').read_text())
    expected=expected_layer(before,after)
    if inventory(installed/'layer')!=expected:raise ValueError('Staged layer changed after installation audit')
    xattrs=original_xattrs(args.iso,marker['offset'])
    overlap=sorted(set(xattrs)&set(expected))
    if overlap:raise ValueError('Cannot shadow original extended attributes omitted during staging: '+', '.join(overlap))
    # The original SquashFS stays unchanged. Its seven capability-bearing files
    # in this base are absent from the app delta, including all shared ancestors.
    size=sum(v.get('bytes',0) for v in expected.values())
    available=os.statvfs(output.parent)
    if available.f_bavail*available.f_frsize<size*2+256*1024**2:raise ValueError('Insufficient space for pack and independent extraction')
    output.mkdir(mode=0o755,exist_ok=False);image=output/'orez-apps.squashfs'
    subprocess.run(['mksquashfs',str(installed/'layer'),str(image),'-noappend','-no-progress',
                    '-processors','2','-mem','256M','-comp','xz','-all-time',str(args.epoch),
                    '-mkfs-time',str(args.epoch)],check=True)
    extracted=output/'roundtrip'
    subprocess.run(['unsquashfs','-no-progress','-processors','2','-d',str(extracted),str(image)],check=True)
    if inventory(extracted)!=expected:raise ValueError('Packed file contents, ownership, modes, links or xattrs differ')
    result={'schema':1,'purpose':'orez-experimental-app-layer','source_iso_sha256':report['source_iso_sha256'],
            'base_status_sha256':report['base_status_sha256'],'installed_status_sha256':report['installed_status_sha256'],
            'profile_sha256':report['profile_sha256'],'layer_sha256':sha(image),'layer_bytes':image.stat().st_size,
            'source_date_epoch':args.epoch,'paths_verified':len(expected),'original_xattr_paths':sorted(xattrs),
            'shadowed_original_xattrs':overlap,'roundtrip_metadata_and_content_equal':True,
            'full_iso_built':False,'boot_tested':False,'installation_approved':False}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['installed','output','marker','iso']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--epoch',type=int,required=True);pack(p.parse_args())
