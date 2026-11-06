#!/usr/bin/env python3
"""Re-read final ISO layers and manifests; integrity checks, not release approval."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
from image_packages import installed, sha
from live_assembly import ROOT, profile, extent, digest_range, verify_components, squash_cat


def main(iso):
    expected = profile()
    spec = importlib.util.spec_from_file_location('media', ROOT / 'build/update-media-checksums.py')
    media = importlib.util.module_from_spec(spec); spec.loader.exec_module(media)
    with tempfile.TemporaryDirectory(prefix='orez-media-audit-') as temp:
        root = Path(temp)
        paths = ['/casper/orez-apps.squashfs', '/casper/orez-install.squashfs',
                 '/casper/orez-assembly.json', '/casper/filesystem.manifest',
                 '/boot/grub/grub.cfg', '/.disk/info', '/md5sum.txt']
        files = {}
        for index, name in enumerate(paths):
            target = root / str(index)
            subprocess.run(['xorriso', '-osirrox', 'on', '-indev', str(iso), '-extract', name, str(target)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            files[name] = target
        record = json.loads(files['/casper/orez-assembly.json'].read_text())
        for flag in ['boot_tested', 'installation_approved', 'release_approved']:
            if record.get(flag) is not False:
                raise ValueError('Build metadata must not self-approve runtime or release gates')
        if record['layers_low_to_high'] != expected['layer_order_low_to_high']:
            raise ValueError('Unexpected live layer order')
        apps, components = files[paths[0]], files[paths[1]]
        if sha(apps) != record['application_layer_sha256'] or sha(components) != record['component_layer_sha256']:
            raise ValueError('Layer hash mismatch')
        status = squash_cat(components, 'var/lib/dpkg/status')
        # This is locally derived verifier context, not a trusted downloaded
        # manifest. verify_components independently enforces the pinned apps,
        # every current OREZ payload byte and unchanged original package records.
        context = root / 'local-check-context.json'
        context.write_text(json.dumps({'purpose': 'orez-dpkg-owned-components',
            'source_profile_sha256': sha(ROOT / 'image/live-assembly.json'),
            'application_status_sha256': expected['app_status_sha256'],
            'layer_sha256': sha(components),
            'installed_status_sha256': hashlib.sha256(status).hexdigest()}))
        status, version = verify_components(apps, components, context)
        packages = installed(status.decode())
        manifest = ''.join(name.split(':')[0] + ' ' + value + '\n' for name, value in sorted(packages.items()))
        if files['/casper/filesystem.manifest'].read_text() != manifest or record['package_count'] != len(packages) or record['component_package_version'] != version:
            raise ValueError('ISO package inventory mismatch')
        offset, size = extent(iso, '/casper/filesystem.squashfs')
        if size != expected['base_filesystem_bytes'] or digest_range(iso, offset, size) != expected['base_filesystem_sha256'] or record['base_filesystem_sha256'] != expected['base_filesystem_sha256']:
            raise ValueError('Underlying base filesystem changed')
        grub = files['/boot/grub/grub.cfg'].read_text()
        kernels = re.findall(r'^\s*linux\s+(/casper/vmlinuz\s+.*)$', grub, re.MULTILINE)
        if len(kernels) != 2 or any(line.split().count('boot=casper') != 1 for line in kernels) or 'layerfs-path=' in grub or 'OEM install' in grub:
            raise ValueError('Boot choices do not require the reviewed live-owner flow')
        if 'installation unavailable' not in grub or 'installation disabled' not in files['/.disk/info'].read_text():
            raise ValueError('Missing visible installation limitation')
        checksums = media.parse(files['/md5sum.txt'].read_text())
        for name, file in files.items():
            if name != '/md5sum.txt' and checksums.get('.' + name) != media.md5(file):
                raise ValueError('Media checksum mismatch: ' + name)
        print('PASS: original base, pinned apps, current dpkg-owned OREZ, all package records, boot flags and additional media checksums')
        print(f'{len(packages)} installed-package records; runtime, Secure Boot, installation and release NOT approved')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('iso', type=Path)
    main(p.parse_args().iso)
