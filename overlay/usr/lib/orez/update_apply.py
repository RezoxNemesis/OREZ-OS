#!/usr/bin/env python3
"""OREZ Update — apply an offline update from an OREZ update USB (runs as root).

Trust chain, all checked here before anything is installed:
  * The update is copied off the USB into a root-only folder first, then every
    file is checked against the update's SHA256SUMS (the USB can't change
    afterwards, and nothing unlisted is used).
  * Ubuntu packages come with Ubuntu's own signed InRelease files. gpgv checks
    them against the Ubuntu archive keyring already on this computer, and apt
    then checks every index and .deb hash itself. A tampered package fails.
  * Only the USB copy is used as a package source (your normal online sources
    are untouched); if that is not enough and the internet is available, apt may
    also use your normal Ubuntu sources, which are signed the same way.
  * NVIDIA drivers are Canonical-built, Canonical-signed kernel modules: no DKMS,
    Secure Boot stays on. Steam is installed only after you accept Valve's
    Steam Subscriber Agreement.
Nothing here opens network ports, adds accounts, or runs in the background.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

STATE = Path('/var/lib/orez/updates.json')
CACHE = Path('/var/cache/orez-update')
LOG = Path('/var/log/orez-update.log')
UBUNTU_KEYRING = Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg')
STEAM_AGREEMENT = 'https://store.steampowered.com/subscriber_agreement/'
SAFE = re.compile(r'[A-Za-z0-9._+~%/-]+')
PKG = re.compile(r'[a-z0-9][a-z0-9+.-]*(:i386|:amd64)?')
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8', 'DEBIAN_FRONTEND': 'noninteractive',
       'DEBCONF_NONINTERACTIVE_SEEN': 'true'}


class UpdateError(Exception):
    pass


def say(message: str) -> None:
    line = time.strftime('%H:%M:%S ') + message
    print(message, flush=True)
    try:
        with LOG.open('a') as f:
            f.write(line + '\n')
    except OSError:
        pass


def step(n: int, total: int, text: str) -> None:
    say(f'STEP {n}/{total} {text}')


def run(args: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    r = subprocess.run(args, env=ENV, text=True, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.STDOUT if capture else None)
    if check and r.returncode != 0:
        tail = (r.stdout or '')[-1500:] if capture else ''
        raise UpdateError(f'{args[0]} failed ({r.returncode}). {tail}')
    return r


# ---------- media and manifest ----------

def find_media(candidates: list[Path] | None = None) -> list[Path]:
    """Mounted OREZ update folders (…/orez-update containing update.json)."""
    if candidates is None:
        candidates = [p for base in (Path('/media'), Path('/run/media')) if base.is_dir() for p in base.glob('*/*')]
        candidates += list(Path('/mnt').glob('*')) if Path('/mnt').is_dir() else []
    roots = candidates
    found = []
    for r in roots:
        d = r / 'orez-update'
        if (d / 'update.json').is_file() and (d / 'SHA256SUMS').is_file():
            found.append(d)
    return found


def parse_sums(text: str) -> dict[str, str]:
    sums: dict[str, str] = {}
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        m = re.fullmatch(r'([0-9a-f]{64}) [ *]([^\0\n]+)', line)
        if not m:
            raise UpdateError(f'SHA256SUMS line {n} is malformed.')
        name = m.group(2)
        if (not SAFE.fullmatch(name) or name.startswith('/') or '..' in name.split('/')
                or name in sums or name == 'SHA256SUMS'):
            raise UpdateError(f'SHA256SUMS lists an unsafe or repeated path: {name!r}')
        sums[name] = m.group(1)
    if 'update.json' not in sums:
        raise UpdateError('SHA256SUMS does not cover update.json.')
    return sums


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load_manifest(text: str) -> dict:
    m = json.loads(text)
    need = {'schema', 'version', 'from_versions', 'suites', 'components', 'packages', 'summary'}
    if not isinstance(m, dict) or not need <= set(m) or m['schema'] != 1:
        raise UpdateError('This is not an OREZ update this version understands.')
    if not re.fullmatch(r'[0-9]+(\.[0-9]+)+', str(m['version'])):
        raise UpdateError('Invalid update version.')
    for key in ('packages', 'steam_packages', 'nvidia_packages'):
        for p in m.get(key, []):
            if not PKG.fullmatch(p):
                raise UpdateError(f'Invalid package name in update: {p!r}')
    for s in m['suites'] + m['components']:
        if not re.fullmatch(r'[a-z0-9-]+', s):
            raise UpdateError('Invalid suite or component name.')
    if m.get('orez_shell') and not re.fullmatch(r'orez-shell_[0-9A-Za-z.+~-]+_all\.deb', m['orez_shell']):
        raise UpdateError('Invalid OREZ package name.')
    return m


def copy_verified(media: Path, dest: Path) -> dict:
    """Copy exactly the files listed in SHA256SUMS to dest, verifying each copy."""
    sums = parse_sums((media / 'SHA256SUMS').read_text())
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, mode=0o700)
    total = sum((media / n).stat().st_size for n in sums)
    done = 0
    last = -1
    for name, want in sorted(sums.items()):
        src = media / name
        if src.is_symlink() or not src.is_file():
            raise UpdateError(f'{name} is missing from the USB or is not a regular file.')
        out = dest / name
        out.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        h = hashlib.sha256()
        with src.open('rb') as fi, out.open('wb') as fo:
            for b in iter(lambda: fi.read(1 << 20), b''):
                h.update(b); fo.write(b); done += len(b)
                pct = int(done * 100 / max(total, 1))
                if pct != last and pct % 5 == 0:
                    say(f'COPY {pct}'); last = pct
        if h.hexdigest() != want:
            raise UpdateError(f'{name} does not match its checksum. The USB copy is damaged; rewrite the USB.')
        os.chmod(out, 0o644)
    for d, _, files in os.walk(dest):
        os.chmod(d, 0o755)
    os.chmod(dest, 0o700)
    return sums


# ---------- system checks ----------

def os_release() -> dict:
    out = {}
    for line in Path('/etc/os-release').read_text().splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            out[k] = v.strip().strip('"')
    return out


def current_version() -> str:
    m = re.search(r'OREZ OS ([0-9.]+)', os_release().get('PRETTY_NAME', ''))
    return m.group(1) if m else ''


def check_system(manifest: dict) -> None:
    if os.geteuid() != 0:
        raise UpdateError('The updater must run as administrator (it is started through pkexec).')
    if 'boot=casper' in Path('/proc/cmdline').read_text().split():
        raise UpdateError('This is the USB live session. Install OREZ first, then apply updates on the installed system.')
    rel = os_release()
    if rel.get('NAME') != 'OREZ OS':
        raise UpdateError('This computer is not running OREZ OS.')
    if os.uname().machine != 'x86_64':
        raise UpdateError('OREZ updates are for 64-bit PCs (x86_64).')
    ver = current_version()
    if ver not in manifest['from_versions'] and ver != manifest['version']:
        raise UpdateError(f'This update is for OREZ {", ".join(manifest["from_versions"])}; this PC runs {ver or "an unknown version"}.')
    free = shutil.disk_usage('/').free
    if free < 12 * 1024 ** 3:
        raise UpdateError(f'Not enough free space: {free // 1024 ** 3} GB free, 12 GB needed.')


def nvidia_gpu(pci: Path = Path('/sys/bus/pci/devices')) -> bool:
    for dev in pci.glob('*') if pci.is_dir() else []:
        try:
            if (dev / 'vendor').read_text().strip() == '0x10de' and (dev / 'class').read_text().strip().startswith('0x03'):
                return True
        except OSError:
            pass
    return False


def installed_nvidia_series() -> str | None:
    r = run(['dpkg-query', '-W', '-f', '${Package} ${db:Status-Status}\n', 'nvidia-driver-*'], check=False, capture=True)
    for line in (r.stdout or '').splitlines():
        name, _, status = line.partition(' ')
        m = re.fullmatch(r'nvidia-driver-([0-9]+(?:-open)?(?:-server)?(?:-open)?)', name)
        if m and status.strip() == 'installed':
            return m.group(1)
    return None


# ---------- apt ----------

def apt_options(work: Path, sources: Path) -> list[str]:
    empty = work / 'apt' / 'empty.d'
    empty.mkdir(parents=True, exist_ok=True)
    for d in ('lists/partial', 'archives/partial'):
        (work / 'apt' / d).mkdir(parents=True, exist_ok=True)
    return ['-o', f'Dir::Etc::SourceList={sources}', '-o', f'Dir::Etc::SourceParts={empty}',
            '-o', f'Dir::Etc::Parts={empty}', '-o', f'Dir::State::Lists={work}/apt/lists',
            '-o', f'Dir::Cache::Archives={work}/apt/archives', '-o', f'Dir::Cache={work}/apt',
            '-o', 'Acquire::Languages=none', '-o', 'Acquire::By-Hash=no',
            '-o', 'APT::Sandbox::User=root', '-o', 'Dpkg::Options::=--force-confdef',
            '-o', 'Dpkg::Options::=--force-confold']


def write_sources(path: Path, mirror: Path, manifest: dict, online: bool) -> None:
    comps = ' '.join(manifest['components'])
    lines = [f'deb [signed-by={UBUNTU_KEYRING} arch=amd64,i386] file:{mirror} {s} {comps}' for s in manifest['suites']]
    if online:
        for s in manifest['suites']:
            uri = 'http://security.ubuntu.com/ubuntu' if s.endswith('-security') else 'http://archive.ubuntu.com/ubuntu'
            lines.append(f'deb [signed-by={UBUNTU_KEYRING} arch=amd64,i386] {uri} {s} {comps}')
    path.write_text('\n'.join(lines) + '\n')


def verify_release_signatures(mirror: Path, manifest: dict) -> None:
    for s in manifest['suites']:
        rel = mirror / 'dists' / s / 'InRelease'
        if not rel.is_file():
            raise UpdateError(f'Missing signed index for {s}.')
        r = run(['gpgv', '--keyring', str(UBUNTU_KEYRING), str(rel)], check=False, capture=True)
        if r.returncode != 0:
            raise UpdateError(f'The Ubuntu signature on {s} is not valid. Nothing was installed.')
    say('Ubuntu archive signatures verified.')


def plan_is_safe(sim: str) -> None:
    inst = [l for l in sim.splitlines() if l.startswith('Inst ')]
    bad = [l for l in inst if re.match(r'Inst (nvidia-dkms|dkms )', l)]
    if bad:
        raise UpdateError('The plan would build drivers with DKMS; refusing (signed prebuilt modules only).')
    removing = [l.split()[1] for l in sim.splitlines() if l.startswith('Remv ')]
    protected = [p for p in removing if p in ('orez-shell', 'plasma-desktop', 'plasma-workspace', 'sddm', 'kubuntu-desktop', 'linux-generic')]
    if protected:
        raise UpdateError('The plan would remove essential packages: ' + ', '.join(protected))


def apt(opts: list[str], *args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return run(['apt-get', *opts, *args], capture=capture, check=not capture)


# ---------- identity ----------

def set_identity(version: str) -> None:
    p = Path('/usr/lib/os-release')
    text = p.read_text()
    text = re.sub(r'^PRETTY_NAME=.*$', f'PRETTY_NAME="OREZ OS {version}"', text, flags=re.M)
    text = re.sub(r'^VERSION=.*$', f'VERSION="{version} (Kubuntu 26.04 base)"', text, flags=re.M)
    p.write_text(text)
    lsb = Path('/etc/lsb-release')
    if lsb.is_file():
        lsb.write_text(re.sub(r'^DISTRIB_DESCRIPTION=.*$', f'DISTRIB_DESCRIPTION="OREZ OS {version}"', lsb.read_text(), flags=re.M))
    Path('/etc/issue').write_text(f'OREZ OS {version} \\n \\l\n\n')
    Path('/etc/issue.net').write_text(f'OREZ OS {version}\n')


def record(entry: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    try:
        hist = json.loads(STATE.read_text())
    except (OSError, ValueError):
        hist = []
    hist.append(entry)
    STATE.write_text(json.dumps(hist, indent=1) + '\n')


# ---------- main ----------

def apply(media: Path, accept_steam: bool, want_nvidia: bool | None, dry_run: bool) -> int:
    total = 7
    step(1, total, 'Checking the update USB')
    manifest_on_usb = load_manifest((media / 'update.json').read_text())
    check_system(manifest_on_usb)
    version = manifest_on_usb['version']
    work = CACHE / version
    say(f'OREZ OS {current_version()} → {version}')

    step(2, total, 'Copying and verifying every file (this takes a few minutes)')
    copy_verified(media, work / 'payload')
    payload = work / 'payload'
    manifest = load_manifest((payload / 'update.json').read_text())
    if manifest != manifest_on_usb:
        raise UpdateError('The update description changed while it was being copied.')
    mirror = payload / 'mirror'

    step(3, total, 'Checking Ubuntu package signatures')
    verify_release_signatures(mirror, manifest)

    step(4, total, 'Preparing 32-bit game support and the package list')
    arches = run(['dpkg', '--print-foreign-architectures'], capture=True).stdout.split()
    if 'i386' not in arches and not dry_run:
        run(['dpkg', '--add-architecture', 'i386'])
        say('Enabled 32-bit (i386) packages for Steam and older Windows games.')
    sources = work / 'sources.list'
    packages = list(manifest['packages'])
    gpu = nvidia_gpu() if want_nvidia is None else want_nvidia
    have = installed_nvidia_series()
    if gpu or want_nvidia:
        if have and have != manifest.get('nvidia_series'):
            packages.append(f'libnvidia-gl-{have.replace("-open", "")}:i386')
            say(f'Keeping your installed NVIDIA driver {have}; adding its 32-bit libraries.')
        else:
            packages += manifest.get('nvidia_packages', [])
            say(f'NVIDIA graphics card found: installing driver {manifest.get("nvidia_series")} (Canonical-signed).')
    else:
        say('No NVIDIA graphics card found: skipping the NVIDIA driver.')
    if accept_steam:
        packages += manifest.get('steam_packages', [])
        sel = '\n'.join(manifest.get('steam_debconf', [])) + '\n'
        subprocess.run(['debconf-set-selections'], input=sel, text=True, env=ENV, check=True)
        say('Steam Subscriber Agreement accepted by the owner.')
    else:
        say('Steam not selected (agreement not accepted). Wine and Lutris are still installed.')
    shell = payload / manifest['orez_shell'] if manifest.get('orez_shell') else None

    online = False
    for attempt in ('usb', 'usb+online'):
        online = attempt == 'usb+online'
        write_sources(sources, mirror, manifest, online)
        opts = apt_options(work, sources)
        r = apt(opts, 'update', capture=True)
        if r.returncode != 0:
            if online:
                raise UpdateError('Reading the package lists failed. ' + (r.stdout or '')[-800:])
            continue
        targets = packages + ([str(shell)] if shell else [])
        sim = apt(opts, '-s', 'install', '-y', *targets, capture=True)
        if sim.returncode == 0:
            break
        say('The USB alone is not enough for this PC: ' + (sim.stdout or '').strip().splitlines()[-1][:300])
        if online:
            raise UpdateError('The update cannot be installed: ' + (sim.stdout or '')[-1200:])
        if run(['sh', '-c', 'getent hosts archive.ubuntu.com >/dev/null'], check=False).returncode != 0:
            raise UpdateError('Some packages are missing on the USB and there is no internet connection to fetch them. '
                              'Connect to the internet and run OREZ Update again.')
        say('Using your internet connection for the missing Ubuntu packages (same Ubuntu signatures).')
    plan_is_safe(sim.stdout)
    n_inst = sum(1 for l in sim.stdout.splitlines() if l.startswith('Inst '))
    say(f'Plan: {n_inst} packages to install or upgrade' + (' (some from the internet)' if online else ' (all from the USB)') + '.')
    if dry_run:
        say('Dry run: nothing installed.')
        return 0

    step(5, total, f'Installing {n_inst} packages (Steam, Wine, drivers, game tools)')
    proc = subprocess.Popen(['apt-get', *opts, 'install', '-y', *targets], env=ENV, text=True,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out_lines = []
    set_up = 0
    with LOG.open('a') as log:
        for line in proc.stdout:
            out_lines.append(line); log.write(line)
            if line.startswith('Setting up '):
                set_up += 1
                say(f'INSTALL {min(99, set_up * 100 // max(n_inst, 1))} {line.split()[2]}')
    output = ''.join(out_lines)
    if proc.wait() != 0:
        raise UpdateError('Package installation failed; see /var/log/orez-update.log. ' + output[-800:])
    if re.search(r'^(Setting up|Unpacking) (nvidia-dkms|dkms)', output, re.M):
        raise UpdateError('DKMS was used unexpectedly; please report this.')

    step(6, total, 'Finishing: OREZ identity and gaming defaults')
    set_identity(version)
    run(['dpkg', '--configure', '-a'])
    audit = run(['dpkg', '--audit'], capture=True).stdout.strip()
    if audit:
        raise UpdateError('The package database is not clean after the update: ' + audit[:600])
    record({'version': version, 'from': manifest['from_versions'], 'time': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'steam': accept_steam, 'nvidia': bool(gpu), 'online_used': online, 'packages': n_inst})

    step(7, total, 'Cleaning up')
    shutil.rmtree(work / 'apt' / 'archives', ignore_errors=True)
    shutil.rmtree(work / 'payload', ignore_errors=True)
    say(f'DONE OREZ OS {version} is installed. Restart the computer to finish.')
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description='Apply an OREZ update from a USB drive.')
    p.add_argument('--media', type=Path, help='the orez-update folder on the USB (default: find it)')
    p.add_argument('--accept-steam-license', action='store_true',
                   help=f'install Steam; you accept the Steam Subscriber Agreement ({STEAM_AGREEMENT})')
    g = p.add_mutually_exclusive_group()
    g.add_argument('--nvidia', dest='nvidia', action='store_true', default=None)
    g.add_argument('--no-nvidia', dest='nvidia', action='store_false')
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args(argv)
    try:
        media = a.media
        if media is None:
            found = find_media()
            if not found:
                raise UpdateError('No OREZ update USB found. Plug it in and open it once in Dolphin so it is mounted.')
            media = found[0]
        if media.name != 'orez-update' and (media / 'orez-update').is_dir():
            media = media / 'orez-update'
        LOG.parent.mkdir(parents=True, exist_ok=True)
        say(f'Update source: {media}')
        return apply(media.resolve(), a.accept_steam_license, a.nvidia, a.dry_run)
    except (UpdateError, OSError, ValueError, KeyError, subprocess.SubprocessError) as e:
        say('FAILED ' + str(e))
        say('Your system was not changed beyond the steps already shown. Fix the problem and run OREZ Update again.')
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
