#!/usr/bin/env python3
"""Compose a CI-built OREZ system layer onto the signed Kubuntu ISO.

Inputs: the signature-verified official ISO, orez-apps.squashfs produced by
ci-build-layer.sh (with its dpkg manifest), and this checkout. Output: a live
ISO whose original /casper/filesystem.squashfs is byte-identical to upstream.
Same initrd owner-setup patch, live-owner layer and GRUB branding as
assemble-live.py; differs only in taking one CI-built package layer instead of
locally pinned, separately reviewed layers.
"""
import argparse, importlib.util, json, os, shutil, subprocess, tempfile
from pathlib import Path
from image_packages import sha
from live_assembly import ROOT, profile, brand_grub, extent, digest_range


def module(name):
    s = importlib.util.spec_from_file_location(name, ROOT / 'build' / (name + '.py'))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


media = module('update-media-checksums'); patch = module('patch-live-initrd')


def extract(iso, name, dest):
    subprocess.run(['xorriso', '-osirrox', 'on', '-indev', str(iso), '-extract', name, str(dest)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(a):
    os.umask(0o022)
    if a.output.exists():
        raise SystemExit('Require a new output ISO')
    if sha(a.iso) != profile()['official_iso_sha256']:
        raise SystemExit('Input is not the pinned official Kubuntu ISO')
    offset, size = extent(a.iso, '/casper/filesystem.squashfs')
    if size != profile()['base_filesystem_bytes'] or digest_range(a.iso, offset, size) != profile()['base_filesystem_sha256']:
        raise SystemExit('Unexpected base filesystem')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='orez-ci-compose-', dir=a.output.parent) as t:
        w = Path(t)
        extract(a.iso, '/casper/initrd', w / 'initrd-original')
        patch.patch(w / 'initrd-original', w / 'initrd', w / 'orez-initrd.json', owner_setup=True)
        import live_splash
        splash_report = live_splash.append(w / 'initrd', ROOT / 'overlay/usr/share/plymouth/themes/orez')
        subprocess.run(['python3', str(ROOT / 'build/stage-overlay.py'), '--source', str(ROOT / 'overlay'),
                        '--output', str(w / 'live'), '--live-owner'], check=True)
        installer_report = None
        if a.enable_installer:
            import ci_installer
            installer_report = ci_installer.stage(w / 'live', a.iso, offset)
        subprocess.run(['mksquashfs', str(w / 'live'), str(w / 'zz-orez.squashfs'), '-noappend', '-no-progress',
                        '-comp', 'xz', '-all-root', '-all-time', '1793923200', '-mkfs-time', '1793923200'], check=True)
        subprocess.run(['python3', str(ROOT / 'build/verify-live-owner.py'), '--source', str(ROOT / 'image/live-owner'),
                        '--squashfs', str(w / 'zz-orez.squashfs')], check=True)
        extract(a.iso, '/boot/grub/grub.cfg', w / 'grub-original.cfg')
        grub = brand_grub((w / 'grub-original.cfg').read_text())
        if a.enable_installer:
            grub = grub.replace('Try OREZ OS (installation unavailable)', 'Try or Install OREZ OS')
        (w / 'grub.cfg').write_text(grub)
        (w / 'info').write_text('OREZ OS 0.1 development amd64 — Kubuntu 26.04.1 base — ' +
                                ('installer enabled — ' if a.enable_installer else '') + 'CI build ' +
                                os.environ.get('OREZ_SOURCE_COMMIT', 'working-tree')[:12] + '\n')
        shutil.copy2(a.manifest, w / 'filesystem.manifest')
        report = {'schema': 1, 'builder': 'ci-overlay', 'parent_sha256': profile()['official_iso_sha256'],
                  'base_filesystem_sha256': profile()['base_filesystem_sha256'],
                  'system_layer_sha256': sha(a.layer), 'live_owner_layer_sha256': sha(w / 'zz-orez.squashfs'),
                  'layers_low_to_high': ['filesystem.squashfs', 'orez-apps.squashfs', 'zz-orez.squashfs'],
                  'source_commit': os.environ.get('OREZ_SOURCE_COMMIT', 'working-tree'),
                  'live_splash': splash_report,
                  'installer_enabled': bool(a.enable_installer), 'installer_config_sha256': installer_report,
                  'boot_tested': False, 'installation_approved': False, 'release_approved': False}
        (w / 'orez-assembly.json').write_text(json.dumps(report, indent=2) + '\n')
        mapped = {'/casper/initrd': w / 'initrd', '/casper/orez-initrd.json': w / 'orez-initrd.json',
                  '/casper/zz-orez.squashfs': w / 'zz-orez.squashfs', '/casper/orez-apps.squashfs': a.layer,
                  '/casper/orez-assembly.json': w / 'orez-assembly.json',
                  '/casper/filesystem.manifest': w / 'filesystem.manifest',
                  '/boot/grub/grub.cfg': w / 'grub.cfg', '/.disk/info': w / 'info'}
        extract(a.iso, '/md5sum.txt', w / 'old-md5sum.txt')
        entries = media.parse((w / 'old-md5sum.txt').read_text())
        entries.update({'.' + name: media.md5(path) for name, path in mapped.items()})
        (w / 'md5sum.txt').write_text(''.join(d + '  ' + n + '\n' for n, d in entries.items()))
        mapped['/md5sum.txt'] = w / 'md5sum.txt'
        cmd = ['xorriso', '-indev', str(a.iso), '-outdev', str(a.output)]
        for name, path in mapped.items():
            cmd += ['-map', str(path), name]
        cmd += ['-boot_image', 'any', 'replay', '-commit']
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        for i, (name, path) in enumerate(mapped.items()):
            c = w / ('checked-' + str(i)); extract(a.output, name, c)
            if sha(c) != sha(path):
                raise SystemExit('ISO mapping differs: ' + name)
            c.unlink()
    o2, s2 = extent(a.output, '/casper/filesystem.squashfs')
    if s2 != size or digest_range(a.output, o2, s2) != profile()['base_filesystem_sha256']:
        raise SystemExit('Original lower filesystem changed')
    report.update(output_sha256=sha(a.output), output_bytes=a.output.stat().st_size, base_filesystem_unchanged=True)
    a.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    a.output.with_suffix('.iso.sha256').write_text(report['output_sha256'] + '  ' + a.output.name + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for n in ['iso', 'layer', 'manifest', 'output']:
        p.add_argument('--' + n, type=Path, required=True)
    p.add_argument('--enable-installer', action='store_true',
                   help='Stage the OREZ installer (for the VM installation test until it is qualified)')
    main(p.parse_args())
