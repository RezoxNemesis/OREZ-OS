#!/usr/bin/env python3
"""Single source of truth for the versioned OREZ native package artifact."""
import argparse
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def version(text=None):
 value=(text if text is not None else (ROOT/'packaging/orez-shell.version').read_text()).strip()
 # Deliberately exclude epochs, slashes, whitespace and shell metacharacters.
 if not re.fullmatch(r'[0-9][A-Za-z0-9.+~]*-[0-9][A-Za-z0-9.+~]*',value):
  raise ValueError('Invalid OREZ Debian version; expected upstream-revision, e.g. 0.1.0-2')
 return value


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('field',choices=['version','filename','path'])
 args=parser.parse_args()
 filename='orez-shell_'+version()+'_all.deb'
 print(version() if args.field=='version' else filename if args.field=='filename' else str(ROOT/'dist'/filename))


if __name__=='__main__':main()
