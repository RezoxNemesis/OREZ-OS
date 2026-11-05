#!/usr/bin/env python3
"""Maintain casper's legacy corruption-detection list for changed OREZ files.

MD5 here is an upstream media-error check, never an authenticity guarantee.
Signed upstream SHA-256 verification and output SHA-256 remain mandatory.
"""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re

NAMES = ('./casper/initrd', './casper/orez-initrd.json',
         './casper/zz-orez.squashfs', './casper/orez-install.squashfs')


def parse(text):
    entries = {}
    for line in text.splitlines():
        match = re.fullmatch(r'([0-9a-f]{32})  (\./\S+)', line)
        if not match:
            raise ValueError('unrecognized media checksum line')
        digest, name = match.groups()
        path = PurePosixPath(name[2:])
        if path.is_absolute() or '..' in path.parts or './' + str(path) != name or name in entries:
            raise ValueError('unsafe or duplicate media checksum path')
        entries[name] = digest
    if './casper/initrd' not in entries:
        raise ValueError('upstream initrd checksum is required')
    return entries


def md5(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'md5').hexdigest()


def update(text, replacements):
    if set(replacements) != set(NAMES):
        raise ValueError('only the four explicit OREZ media paths may be updated')
    entries = parse(text)
    entries.update({name: md5(path) for name, path in replacements.items()})
    return ''.join(f'{digest}  {name}\n' for name, digest in entries.items())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    for option in ['initrd', 'metadata', 'live', 'install']:
        parser.add_argument('--' + option, type=Path, required=True)
    args = parser.parse_args()
    result = update(args.source.read_text(), dict(zip(NAMES, [args.initrd, args.metadata, args.live, args.install])))
    with args.output.open('x') as stream:
        stream.write(result)
    print('Updated four local media checksums; all unrelated entries preserved. MD5 is not authentication.')
