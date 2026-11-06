#!/usr/bin/env python3
"""Prepare an isolated package-test root from verified caller-selected ISO bytes.

This does not authenticate a release signature: the outer ISO builder must do
that first. Original /dev and other runtime mounts and source xattrs are omitted
ONLY from this temporary chroot. It must not be shipped as a replacement base.
An additive layer preserves unchanged original-base files and their metadata.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
from image_packages import sha


def require_build_container():
    mapping=Path('/proc/self/uid_map').read_text().splitlines()[0].split()
    if os.geteuid()!=0 or not Path('/.dockerenv').is_file() or int(mapping[1])==0:
        raise ValueError('Use a disposable rootless image-tools container, never host root')


def work_path(path):
    path=Path(path).absolute()
    if path.parent!=Path('/work') or path.name in ['', '.', '..'] or any(p.is_symlink() for p in [path,*path.parents]):
        raise ValueError('Staging must be a new direct child of the task-owned /work mount')
    return path


def stage(args):
    require_build_container();root=work_path(args.output)
    if root.exists() or root.with_suffix('.orez-build.json').exists():raise ValueError('Require new staging paths')
    if args.iso.is_symlink() or not args.iso.is_file() or sha(args.iso)!=args.expected_iso_sha256:
        raise ValueError('ISO differs from the explicitly verified input identity')
    if args.offset<0 or args.offset%2048:raise ValueError('Invalid SquashFS offset')
    with args.iso.open('rb') as stream:
        stream.seek(args.offset)
        if stream.read(4)!=b'hsqs':raise ValueError('No SquashFS at the reviewed offset')
    listing=subprocess.check_output(['unsquashfs','-lln','-o',str(args.offset),str(args.iso)],text=True)
    size=sum(int(p[2]) for line in listing.splitlines() if len(p:=line.split(maxsplit=5))==6 and p[0].startswith('-'))
    space=os.statvfs(root.parent)
    if space.f_bavail*space.f_frsize<size+1024**3:raise ValueError('Insufficient staging space including package reserve')
    subprocess.run(['unsquashfs','-no-progress','-processors','2','-no-xattrs','-excludes','-o',str(args.offset),'-d',str(root),str(args.iso),'dev','proc','sys','run','tmp'],check=True)
    for name,mode in [('dev',0o755),('proc',0o755),('sys',0o755),('run',0o755),('tmp',0o1777)]:
        path=root/name;path.mkdir();path.chmod(mode)
    metadata={'schema':1,'purpose':'orez-additive-package-staging','root':str(root),
              'input_iso_sha256':args.expected_iso_sha256,'offset':args.offset,
              'base_status_sha256':sha(root/'var/lib/dpkg/status'),'root_is_complete_release_filesystem':False,
              'omitted_runtime_trees':['dev','proc','sys','run','tmp'],'source_xattrs_in_staging':False,
              'installation_approved':False}
    root.with_suffix('.orez-build.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--iso',type=Path,required=True)
    p.add_argument('--expected-iso-sha256',required=True);p.add_argument('--offset',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    stage(p.parse_args())
