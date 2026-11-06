#!/usr/bin/env python3
"""Generate an INACTIVE Calamares configuration from exact reviewed source files.

No installer activation, disk access, chroot, root command or network operation.
Changed upstream bytes require review. Output is a new staging directory only.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

from image_packages import installed
from live_assembly import ROOT, profile as live_profile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def render(source, rules):
    data = source
    for before, after in rules['replacements']:
        if not before or data.count(before) != 1:
            raise ValueError('Configuration replacement is ambiguous or stale')
        data = data.replace(before, after)
    if digest(data.encode()) != rules['expected_output_sha256']:
        raise ValueError('Generated configuration differs from reviewed output')
    return data


def prepare(source, status, output, profile_path=ROOT / 'image/installer/profile.json'):
    value = json.loads(profile_path.read_text())
    if (value['schema'] != 1 or value['purpose'] != 'orez-inactive-installer-profile'
            or value['installation_approved'] is not False
            or value['base_filesystem_sha256'] != live_profile()['base_filesystem_sha256']):
        raise ValueError('Unrecognized installer source profile')
    if source.is_symlink() or not source.is_dir() or status.is_symlink() or not status.is_file():
        raise ValueError('Use regular source directory and base package status')
    if digest(status.read_bytes()) != live_profile()['base_status_sha256']:
        raise ValueError('Base package state differs from reviewed image')
    packages = installed(status.read_text())
    for name, version in {**value['required_installed_packages'], 'calamares': value['calamares_version']}.items():
        if packages.get(name + ':amd64') != version:
            raise ValueError('Required installer/bootloader package differs: ' + name)
    original = {}
    for name, expected in value['source_config_sha256'].items():
        relative = PurePosixPath(name)
        path = source / name
        if relative.is_absolute() or '..' in relative.parts or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError('Unsafe installer source path')
        if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError('Unreviewed installer configuration: ' + name)
        original[name] = path.read_text()
    generated = {name: render(original[name], rules) for name, rules in value['changes'].items()}
    unpack = (ROOT / 'image/installer/orez-unpackfs-candidate.conf').read_bytes()
    if digest(unpack) != value['unpack_candidate_sha256']:
        raise ValueError('Unreviewed unpack source sequence')
    generated['etc/calamares/modules/unpackfs.conf'] = unpack.decode()
    # Do not use this build helper to place a configuration in a running OS.
    target = output.absolute()
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents]):
        raise ValueError('Require a new unaliased staging directory')
    target = target.resolve()
    if any(target.is_relative_to(Path(p)) for p in ['/etc', '/usr', '/boot', '/var']):
        raise ValueError('Refusing a system configuration destination')
    target.mkdir(parents=False)
    identities = {}
    for name, content in generated.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(0o644)
        identities[name] = digest(content.encode())
    record = {'purpose': value['purpose'], 'profile_sha256': digest(profile_path.read_bytes()),
              'base_status_sha256': digest(status.read_bytes()),
              'generated_config_sha256': identities,
              'requires_unchanged_upstream_config': sorted(
                  name for name in set(original) - set(generated)
                  if name.startswith('etc/calamares/')),
              'installation_approved': False, 'activated': False,
              'limitations': value['limitations']}
    (target / 'profile-report.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--base-status', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        prepare(args.source, args.base_status, args.output)
    except (OSError, ValueError, KeyError) as error:
        print('Installer profile preparation refused: ' + str(error), file=sys.stderr)
        sys.exit(1)
