#!/usr/bin/env python3
"""Read-only live-owner bytes/ownership/mode audit; never a boot qualification."""
import argparse
from pathlib import Path, PurePosixPath
import subprocess


def verify_metadata(listing, files):
    metadata={}
    for line in listing.splitlines():
        parts=line.split(maxsplit=5)
        if len(parts)==6 and parts[5].startswith('squashfs-root'):
            metadata[parts[5]]=(parts[0],parts[1])
    expected={'squashfs-root':'drwxr-xr-x'}
    for name in files:
        path=PurePosixPath('squashfs-root')/name
        expected[str(path)]='-rw-r--r--'
        for parent in path.parents:
            if str(parent)!='.':expected[str(parent)]='drwxr-xr-x'
    for path,mode in expected.items():
        if metadata.get(path)!=(mode,'0/0'):
            raise ValueError('Untrusted live-owner metadata: '+path)


def verify(source, squashfs):
    files={str(p.relative_to(source)):p for p in source.rglob('*') if p.is_file()}
    if not files:raise ValueError('Missing live-owner source')
    listing=subprocess.check_output(['unsquashfs','-lln',str(squashfs)],text=True)
    verify_metadata(listing, files)
    for relative,path in files.items():
        if path.is_symlink():raise ValueError('Aliased live-owner source')
        data=subprocess.check_output(['unsquashfs','-cat',str(squashfs),relative])
        if data!=path.read_bytes():raise ValueError('Changed live-owner bytes: '+relative)
    print('PASS: live-owner bytes, root ownership and canonical permissions; boot/authentication unqualified')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--squashfs',type=Path,required=True)
    args=parser.parse_args();verify(args.source,args.squashfs)
