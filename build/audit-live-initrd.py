#!/usr/bin/env python3
"""Read known casper authentication hooks; never execute or modify them.

This is a narrow release-blocker detector, not a full policy evaluator. Even a
clean source result cannot establish effective sudo/Polkit or installed security.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def inspect(root):
    root = Path(root).resolve()
    contents = {}
    for name in ['25adduser', '44pk_allow_ubuntu']:
        path = root / 'scripts/casper-bottom' / name
        if not path.is_file() or path.is_symlink() or root not in path.resolve().parents:
            raise ValueError(f'missing or escaping authentication hook: {name}; review required')
        contents[name] = path.read_text()
    findings = []
    for code, name, needle, implication in [
        ('PASSWORDLESS_SUDO', '25adduser', 'NOPASSWD: ALL', 'live-user command elevation without owner authentication'),
        ('BLANK_LIVE_PASSWORD', '25adduser', 'passwd/user-password-crypted U6aMy0wojraho', 'known upstream empty live-user password'),
        ('WILDCARD_POLKIT', '44pk_allow_ubuntu', 'Action=*', 'wildcard live-user PolicyKit grant requires effective-policy review'),
    ]:
        lines = [number for number, text in enumerate(contents[name].splitlines(), 1) if needle in text]
        if lines:
            findings.append({'code': code, 'hook': name, 'lines': lines, 'implication': implication})
    return {'schema_version': 1, 'scope': 'Known upstream initrd source hooks only',
            'status': 'BLOCKED' if findings else 'NO_KNOWN_SOURCE_PATTERN_REQUIRES_RUNTIME_REVIEW',
            'findings': findings,
            'hook_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in contents.items()},
            'effective_policy_tested': False, 'owner_authentication_qualified': False,
            'installation_approved': False,
            'next_gate': 'Review all initrd/live grants and test owner-authenticated sudo/Polkit before sensitive live use.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = inspect(args.root)
        with args.report.open('x') as stream:
            stream.write(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        sys.exit(1 if report['findings'] else 0)
    except (OSError, ValueError) as error:
        print(f'Live authentication audit failed closed: {error}', file=sys.stderr)
        sys.exit(2)
