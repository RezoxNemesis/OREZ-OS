"""Live installer configuration for CI images built with --enable-installer.

Reads the exact Kubuntu Calamares files from the verified ISO, applies the
reviewed OREZ profile (image/installer/profile.json, source and output hashes
still enforced), then the install-time additions: merged-source unpack, OREZ
branding, and the source mount/unmount steps around unpackfs.
"""
import hashlib, importlib.util, json, re, shutil, subprocess
from pathlib import Path

from image_packages import installed
from live_assembly import ROOT, profile as live_profile

_spec = importlib.util.spec_from_file_location('prepare_profile', ROOT / 'build/prepare-installer-profile.py')
_prep = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_prep)

SETTINGS_ADDITIONS = [
    ('- id: rmcdrom\n  module: shellprocess\n  config: shellprocess_rmcdrom.conf\n',
     '- id: rmcdrom\n  module: shellprocess\n  config: shellprocess_rmcdrom.conf\n'
     '- id: orez_source\n  module: shellprocess\n  config: shellprocess_orez_source.conf\n'
     '- id: orez_source_done\n  module: shellprocess\n  config: shellprocess_orez_source_done.conf\n'),
    ('  - unpackfs\n', '  - shellprocess@orez_source\n  - unpackfs\n  - shellprocess@orez_source_done\n'),
    ('branding: kubuntu\n', 'branding: orez\n'),
]


def _cat(iso, offset, name):
    return subprocess.check_output(['unsquashfs', '-o', str(offset), '-cat', str(iso), name], stderr=subprocess.DEVNULL)


def generate(iso, offset):
    value = json.loads((ROOT / 'image/installer/profile.json').read_text())
    status = _cat(iso, offset, 'var/lib/dpkg/status')
    if hashlib.sha256(status).hexdigest() != live_profile()['base_status_sha256']:
        raise ValueError('Base package state differs from reviewed image')
    packages = installed(status.decode())
    for name, version in {**value['required_installed_packages'], 'calamares': value['calamares_version']}.items():
        if packages.get(name + ':amd64') != version:
            raise ValueError('Required installer/bootloader package differs: ' + name)
    out = {}
    for name, rules in value['changes'].items():
        data = _cat(iso, offset, name)
        if hashlib.sha256(data).hexdigest() != value['source_config_sha256'][name]:
            raise ValueError('Unreviewed installer configuration: ' + name)
        out[name] = _prep.render(data.decode(), rules)
    settings = out['etc/calamares/settings.conf']
    for before, after in SETTINGS_ADDITIONS:
        if settings.count(before) != 1:
            raise ValueError('Installer settings addition is ambiguous: ' + before.strip())
        settings = settings.replace(before, after)
    out['etc/calamares/settings.conf'] = settings
    # Partition/filesystem labels: OREZ instead of the upstream flavour name.
    part = out['etc/calamares/modules/partition.conf']
    out['etc/calamares/modules/partition.conf'] = re.sub(r'kubuntu_\d+', 'OREZ', part)
    return out


def stage(live_dir, iso, offset):
    """Turn the live staging tree into an installer-enabled one."""
    live = Path(live_dir)
    for guard in ['usr/bin/calamares', 'usr/share/applications/calamares.desktop']:
        (live / guard).unlink(missing_ok=True)
    src = ROOT / 'image/live-installer'
    for item in src.rglob('*'):
        if item.is_file():
            target = live / item.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            rel = item.relative_to(src).as_posix()
            target.chmod(0o755 if rel.startswith(('usr/bin/', 'usr/lib/orez/orez-install-source')) else 0o644)
    report = {}
    for name, content in generate(iso, offset).items():
        target = live / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content); target.chmod(0o644)
        report[name] = hashlib.sha256(content.encode()).hexdigest()
    return report
