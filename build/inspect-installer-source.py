#!/usr/bin/env python3
"""Read the actual integrated ISO installer configuration without mounting disks.

The expected SHA binds the caller-selected artifact; it is not release-signature
authentication. Passing this inspection never approves installation.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

from image_packages import sha
from live_assembly import ROOT, extent

CONFIGS = (
    'etc/calamares/settings.conf',
    'etc/calamares/modules/unpackfs.conf',
    'etc/calamares/modules/users.conf',
    'etc/calamares/modules/partition.conf',
    'etc/calamares/modules/bootloader.conf',
    'etc/calamares/modules/packages.conf',
    'etc/sysctl.d/20-apparmor.conf',
)


def assess(configs, guard_matches):
    """Report exact observed source and unresolved gates, never a safety pass."""
    unpack = configs.get('etc/calamares/modules/unpackfs.conf', '')
    sources = re.findall(r'^\s*-?\s*source:\s*[\"\']?([^\"\'\s#]+)', unpack, re.M)
    required = ['/cdrom/casper/' + name for name in
                ['filesystem.squashfs', 'orez-apps.squashfs', 'orez-install.squashfs']]
    blockers = []
    if sources != required:
        blockers.append('active_unpack_sources_do_not_match_integrated_layers')
    override = configs.get('etc/sysctl.d/20-apparmor.conf', '')
    if re.search(r'^\s*kernel\.apparmor_restrict_unprivileged_userns\s*=\s*0\s*(?:#.*)?$', override, re.M):
        blockers.append('base_contains_live_apparmor_override_exclusion_needs_validation')
    if not guard_matches:
        blockers.append('live_installer_guard_not_verified')
    missing = [name for name in CONFIGS[:5] if name not in configs]
    if missing:
        blockers.append('required_installer_configuration_missing')
    return {'status': 'inspection-complete-installation-blocked',
            'active_unpack_sources': sources, 'required_unpack_sources': required,
            'missing_configuration': missing, 'live_guard_matches_source': guard_matches,
            'configuration_blockers': blockers,
            'runtime_gates': ['owner account and administrator policy',
                              'explicit target confirmation and non-target preservation',
                              'actual install and UEFI reboot', 'encryption and recovery',
                              'effective installed AppArmor policy'],
            'installation_approved': False, 'release_approved': False}


def inspect(iso, expected_sha, output):
    if iso.is_symlink() or not iso.is_file() or not re.fullmatch('[0-9a-f]{64}', expected_sha):
        raise ValueError('Require a regular ISO and an explicit lowercase SHA-256')
    if sha(iso) != expected_sha:
        raise ValueError('ISO digest mismatch')
    if output.exists() or any(p.is_symlink() for p in [output, *output.parents]):
        raise ValueError('Require a new unaliased output directory')
    output.mkdir(parents=True)
    # Current verifier knows the four intentional dpkg database additions and
    # proves all pre-existing package records unchanged. The legacy path-only
    # collision checker cannot validate this transaction and is not substituted.
    spec = importlib.util.spec_from_file_location('integrated_media', ROOT / 'build/verify-integrated-media.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verifier.main(iso)
    base_offset, _ = extent(iso, '/casper/filesystem.squashfs')
    live_offset, _ = extent(iso, '/casper/zz-orez.squashfs')
    # Include the real distro-specific process contexts too: otherwise an
    # apparently offline sequence might still execute an unseen network step.
    listing = subprocess.check_output(['unsquashfs', '-ls', '-o', str(base_offset),
                                       str(iso), 'etc/calamares'], text=True, timeout=60)
    names = set(CONFIGS)
    for line in listing.splitlines():
        if not line.startswith('squashfs-root/etc/calamares/') or not line.endswith('.conf'):
            continue
        name = line.removeprefix('squashfs-root/')
        if '..' in PurePosixPath(name).parts or not re.fullmatch(r'[A-Za-z0-9_./#-]+', name):
            raise ValueError('Unexpected installer configuration pathname')
        names.add(name)
    configs, identities, read_errors = {}, {}, {}
    for name in sorted(names):
        result = subprocess.run(['unsquashfs', '-o', str(base_offset), '-cat', str(iso), name],
                                capture_output=True, timeout=60)
        if result.returncode:
            read_errors[name] = result.stderr.decode(errors='replace')[:2000]
            continue
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result.stdout)
        identities[name] = hashlib.sha256(result.stdout).hexdigest()
        configs[name] = result.stdout.decode()
    guard = subprocess.run(['unsquashfs', '-o', str(live_offset), '-cat', str(iso), 'usr/bin/calamares'],
                           capture_output=True, timeout=60)
    guard_matches = guard.returncode == 0 and guard.stdout == (ROOT / 'overlay/usr/bin/calamares').read_bytes()
    result = assess(configs, guard_matches)
    result.update(iso_sha256=expected_sha, iso_bytes=iso.stat().st_size,
                  integrated_media_verified=True, config_sha256=identities,
                  config_read_errors=read_errors, base_read_offset=base_offset,
                  fresh_release_signature_check=False,
                  note='Reads immutable image files only. No mount, installer execution, disk mutation or safety certification.')
    (output / 'INSTALLER_READINESS.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if missing := result['missing_configuration']:
        raise ValueError('Missing required source configuration: ' + ', '.join(missing))
    if not guard_matches:
        raise ValueError('Current live installer guard differs')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('iso', type=Path)
    p.add_argument('--sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        inspect(args.iso, args.sha256, args.output)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('Installer source inspection failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
