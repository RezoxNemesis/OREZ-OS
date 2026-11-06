#!/usr/bin/env python3
"""Resolve the inactive installer's removals against the actual installed inventory.

Offline dependency simulation only: no repositories, downloads, package commits,
maintainer scripts, installer activation or target-disk operations. Run with
python3-apt in the network-isolated image-tools environment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from image_packages import installed

PREFIX = 'update_db: false\nignore_update_db_error: false\nbackend: apt\noperations:\n  - remove:\n'


def removal_names(text):
    if not text.startswith(PREFIX):
        raise ValueError('Only the reviewed offline removal-only configuration is supported')
    names = []
    for line in text[len(PREFIX):].splitlines():
        match = re.fullmatch(r'      - ([a-z0-9][a-z0-9+.-]+)', line)
        if not match or match[1] in names:
            raise ValueError('Ambiguous or unsupported package operation')
        names.append(match[1])
    if not names:
        raise ValueError('No removal operations')
    return names


def validate_plan(requested, changes, broken):
    if broken:
        raise ValueError('Package dependencies remain broken')
    if any(c['operation'] != 'remove' for c in changes):
        raise ValueError('Installer removal unexpectedly changes or installs a package')
    if {c['name'] for c in changes} != set(requested) or len(changes) != len(requested):
        raise ValueError('Installer removal would affect packages outside the exact requested set')


def check(status, expected, config, output):
    for path in [status, config]:
        if path.is_symlink() or not path.is_file():
            raise ValueError('Use regular package status and configuration files')
    status_data = status.read_bytes()
    actual = hashlib.sha256(status_data).hexdigest()
    if actual != expected:
        raise ValueError('Package status digest mismatch')
    before = installed(status_data.decode())
    requested = removal_names(config.read_text())
    target = output.absolute()
    if any(p.is_symlink() for p in [target, *target.parents]) or target.exists():
        raise ValueError('Use a new unaliased result directory')
    target = target.resolve()
    if any(c in str(target) for c in ['"', '\n', '\r', '\\']):
        raise ValueError('Unsafe APT staging path')
    target.mkdir(parents=False)
    with tempfile.TemporaryDirectory(prefix='apt-simulation-', dir=target) as directory:
        root = Path(directory)
        for name in ['etc/apt/apt.conf.d', 'etc/apt/sources.list.d', 'etc/apt/preferences.d',
                     'etc/apt/trusted.gpg.d', 'var/lib/dpkg', 'var/lib/apt/lists/partial',
                     'var/cache/apt/archives/partial']:
            (root / name).mkdir(parents=True, exist_ok=True)
        (root / 'var/lib/dpkg/status').write_bytes(status_data)
        (root / 'etc/apt/sources.list').write_text('')
        cfg = root / 'etc/apt/apt.conf'
        cfg.write_text(f'''Dir "{root}";
Dir::State::status "{root}/var/lib/dpkg/status";
Dir::Etc::trusted "/dev/null";
APT::Architecture "amd64";
APT::Architectures {{ "amd64"; }};
APT::Install-Recommends "false";
APT::Install-Suggests "false";
''')
        os.environ['APT_CONFIG'] = str(cfg)
        import apt
        import apt_pkg
        apt_pkg.config.clear('')
        apt_pkg.init_config()
        cache = apt.Cache(rootdir=str(root), memonly=True)
        initial_broken = cache.broken_count
        if initial_broken:
            raise ValueError('Input package inventory already has broken dependencies')
        for name in requested:
            if name not in cache or not cache[name].is_installed:
                raise ValueError('Requested removal is not installed: ' + name)
            cache[name].mark_delete(auto_fix=True, purge=False)
        changes = [{'name': p.name, 'version': p.installed.version if p.installed else None,
                    'operation': 'remove' if p.marked_delete else 'unexpected-change'}
                   for p in sorted(cache.get_changes(), key=lambda p: p.name)]
        record = {'purpose': 'orez-offline-installer-removal-simulation',
                  'status_sha256': actual, 'installed_records': len(before),
                  'config_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
                  'requested': requested, 'changes': changes, 'broken_count': cache.broken_count,
                  'packages_installed_or_removed': False, 'installation_approved': False,
                  'limitations': ['Installed dependency graph only; no package maintainer scripts executed.',
                                  'No Calamares execution, target filesystem or reboot qualification.']}
        (target / 'removal-plan.json').write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps(record, indent=2), flush=True)
        validate_plan(requested, changes, cache.broken_count)
        cache.close()
    if status.read_bytes() != status_data:
        raise ValueError('Input package status changed during the check')
    print('PASS: only the exact installer/live packages would be removed; all other installed packages retained.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--status', type=Path, required=True)
    p.add_argument('--sha256', required=True)
    p.add_argument('--packages-conf', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        check(a.status, a.sha256, a.packages_conf, a.output)
    except (ValueError, OSError, KeyError) as error:
        print('Installer removal simulation refused: ' + str(error), file=sys.stderr)
        sys.exit(1)
