#!/usr/bin/env python3
"""Replace reviewed cache/optional owner hooks in the pinned final CPIO archive.

Early archives (including microcode) remain byte-identical. Restoring the old
hooks must reconstruct the exact original final archive. Nothing is executed,
mounted or installed; changed upstream inputs require a new explicit review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_INITRD_SHA256 = '0d34300a307d5dd3fbb0ff61e5b43ee3887bcc2d0f6523d600714767f6df4092'
PREFIX_BYTES = 67781012
PREFIX_SHA256 = '13b059f89af0ef4ca98d61cdead9dc37d7b766bcde1bc1e62b929d9737b0b993'
ARCHIVE_SHA256 = '305d97687a6f10426c718e6fb637b81be4a8424e07d87141353d68dcce6d19c6'
ORIGINAL_HOOK_SHA256 = 'fd3768b7b303b61cefe52fb00c9452738f7f83e98ebe4834f9dc61092f7a66fa'
HOOK = 'scripts/casper-bottom/41apt_build_cache_cdrom'
MAX_INITRD_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_BYTES = 72 * 1024 * 1024
OWNER_HOOKS = {
    '15autologin': 'd0e16be3af7de4fc8731fa6f46444a83c1869dda41b36ba3de1edac250ca647e',
    '25adduser': '59a8ca5cd3fc469a892148a7b69562cff2c3b23d82ea2552278fffa48fc96ae3',
    '44pk_allow_ubuntu': '603fb48837b36aa25679ab9cc1bf88b50680d331610e6d18fb43bd9e53b3f9d0',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_initrd(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INITRD_BYTES:
        raise ValueError('require a bounded regular initrd input')
    return path.read_bytes()


def unpack(data):
    # A verifier may receive untrusted input. Bound decoder memory, CPU/wall
    # time and output size; do not extract any paths or run initramfs scripts.
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_ARCHIVE_BYTES, MAX_ARCHIVE_BYTES))
    with tempfile.TemporaryFile() as output:
        subprocess.run(['zstd', '-d', '-q', '-M256MB', '-c'], input=data,
                       stdout=output, check=True, timeout=30, preexec_fn=limits)
        output.seek(0)
        return output.read(MAX_ARCHIVE_BYTES)


def pack(data):
    # The bounded, pinned archive can exceed 30s under contention on small QA
    # hosts. Keep a finite deadline; do not change decoder limits or integrity.
    return subprocess.check_output(['zstd', '-q', '-3', '-T1', '-c'], input=data, timeout=120)


def replace_hook(data, expected, replacement, member=HOOK):
    """Keep every unrelated newc byte/metadata field, including any padding."""
    pos, matches, result = 0, 0, []
    while pos < len(data):
        header = data[pos:pos + 110]
        if len(header) != 110 or header[:6] != b'070701':
            raise ValueError('invalid newc archive header')
        fields = [int(header[6+i*8:14+i*8], 16) for i in range(13)]
        size, namesize = fields[6], fields[11]
        start = pos + 110
        if namesize < 1 or start + namesize > len(data):
            raise ValueError('invalid newc member name size')
        name = data[start:start + namesize]
        if not name.endswith(b'\0') or b'\0' in name[:-1]:
            raise ValueError('invalid newc member name')
        payload = (start + namesize + 3) & ~3
        end = (payload + size + 3) & ~3
        if end > len(data):
            raise ValueError('truncated newc member')
        if name == member.encode() + b'\0':
            matches += 1
            if (fields[1] != stat.S_IFREG | 0o755 or fields[2:5] != [0, 0, 1]
                    or data[payload:payload + size] != expected):
                raise ValueError('hook bytes or metadata differ from reviewed input')
            if any(data[payload + size:end]):
                raise ValueError('unexpected hook padding')
            new_header = header[:54] + f'{len(replacement):08X}'.encode() + header[62:]
            result.append(new_header + data[pos + 110:payload] + replacement
                          + b'\0' * (-len(replacement) % 4))
        else:
            result.append(data[pos:end])
        if name == b'TRAILER!!!\0':
            if size or any(data[end:]) or matches != 1:
                raise ValueError('require one hook and a single complete newc archive')
            result.append(data[end:])
            return b''.join(result)
        pos = end
    raise ValueError('missing newc trailer')


def sources():
    old = (ROOT / 'third_party/casper/41apt_build_cache_cdrom').read_bytes()
    if sha(old) != ORIGINAL_HOOK_SHA256:
        raise ValueError('original hook source digest mismatch')
    return old, (ROOT / 'image/initramfs' / HOOK).read_bytes()


def owner_sources():
    changes = []
    for name, digest in OWNER_HOOKS.items():
        old = (ROOT / 'third_party/casper' / name).read_bytes()
        if sha(old) != digest:
            raise ValueError('original owner hook digest mismatch: ' + name)
        member = 'scripts/casper-bottom/' + name
        changes.append((member, old, (ROOT / 'image/initramfs' / member).read_bytes()))
    return changes


def patch(source, output, report, owner_setup=False):
    source, output, report = map(Path, (source, output, report))
    if output.exists() or output.is_symlink() or report.exists() or report.is_symlink():
        raise ValueError('require new output/report paths')
    if output.resolve() == report.resolve():
        raise ValueError('output and report must differ')
    original = read_initrd(source)
    if sha(original) != EXPECTED_INITRD_SHA256:
        raise ValueError('unrecognized initrd digest; review changed upstream before patching')
    if sha(original[:PREFIX_BYTES]) != PREFIX_SHA256:
        raise ValueError('early initrd prefix digest mismatch')
    plain = unpack(original[PREFIX_BYTES:])
    if sha(plain) != ARCHIVE_SHA256:
        raise ValueError('original final CPIO digest mismatch')
    old, new = sources()
    changed = replace_hook(plain, old, new)
    if replace_hook(changed, new, old) != plain:
        raise ValueError('archive change is not exactly reversible')
    owner_changes = owner_sources() if owner_setup else []
    for member, previous, replacement in owner_changes:
        before = changed
        changed = replace_hook(changed, previous, replacement, member)
        if replace_hook(changed, replacement, previous, member) != before:
            raise ValueError('owner hook change is not exactly reversible')
    patched = original[:PREFIX_BYTES] + pack(changed)
    metadata = {'schema_version': 3 if owner_setup else 2, 'original_sha256': sha(original), 'original_bytes': len(original),
                'patched_sha256': sha(patched), 'patched_bytes': len(patched),
                'early_prefix_bytes': PREFIX_BYTES, 'early_prefix_sha256': PREFIX_SHA256,
                'original_archive_sha256': ARCHIVE_SHA256, 'patched_archive_sha256': sha(changed),
                'replacement': HOOK, 'hook_sha256': sha(new), 'compression': 'zstd',
                'compressor_version': subprocess.check_output(['zstd', '--version'], text=True).strip(),
                'owner': '0:0', 'mode': '0755', 'licence': 'GPL-2.0-or-later',
                'runtime_tested': False, 'secure_boot_qualified': False,
                'administrator_policy_changed': owner_setup, 'installation_approved': False}
    if owner_setup:
        metadata['owner_setup'] = {
            'profile': 'local-console-volatile-live-v1',
            'hooks': {member: sha(replacement) for member, previous, replacement in owner_changes},
            'requires_live_payload': True, 'effective_policy_tested': False,
        }
    with output.open('xb') as stream:
        stream.write(patched)
    output.chmod(0o644)
    with report.open('x') as stream:
        stream.write(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata, indent=2))
    return metadata


def verify(source, report):
    data = read_initrd(source)
    metadata = json.loads(Path(report).read_text())
    if not isinstance(metadata, dict):
        raise ValueError('manifest must be an object')
    if (metadata.get('schema_version') not in [2, 3] or metadata.get('early_prefix_bytes') != PREFIX_BYTES
            or sha(data[:PREFIX_BYTES]) != PREFIX_SHA256):
        raise ValueError('early initrd prefix/manifest mismatch')
    plain = unpack(data[PREFIX_BYTES:])
    old, new = sources()
    restored = replace_hook(plain, new, old)
    owner_setup = metadata['schema_version'] == 3
    if owner_setup:
        expected_owner = {'profile': 'local-console-volatile-live-v1',
                          'hooks': {member: sha(replacement) for member, previous, replacement in owner_sources()},
                          'requires_live_payload': True, 'effective_policy_tested': False}
        if metadata.get('owner_setup') != expected_owner:
            raise ValueError('owner setup manifest differs from reviewed sources')
        for member, previous, replacement in owner_sources():
            restored = replace_hook(restored, replacement, previous, member)
    if sha(restored) != ARCHIVE_SHA256:
        raise ValueError('unexpected unrelated changes to final archive')
    expected = {'original_sha256': EXPECTED_INITRD_SHA256, 'early_prefix_sha256': PREFIX_SHA256,
                'original_archive_sha256': ARCHIVE_SHA256, 'patched_archive_sha256': sha(plain),
                'patched_sha256': sha(data), 'patched_bytes': len(data), 'replacement': HOOK,
                'hook_sha256': sha(new), 'administrator_policy_changed': owner_setup,
                'installation_approved': False, 'secure_boot_qualified': False, 'runtime_tested': False}
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError('patched initrd manifest differs from verified content')
    print('PASS: early archives unchanged; reviewed hook replacements reversible; effective authentication/runtime unqualified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--owner-setup', action='store_true', help='Include reviewed owner/authentication hooks; live payload required')
    args = parser.parse_args()
    if args.verify == bool(args.output):
        parser.error('choose either --verify or --output')
    if args.verify and args.owner_setup:
        parser.error('verification reads the profile from the manifest')
    try:
        if args.verify:
            verify(args.input, args.report)
        else:
            patch(args.input, args.output, args.report, args.owner_setup)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Initrd patch refused: {error}', file=sys.stderr)
        sys.exit(1)
