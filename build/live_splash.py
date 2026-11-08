"""Append the OREZ boot splash to a live initrd as an extra newc archive.

Linux unpacks concatenated initramfs archives in order; later entries win.
The patched upstream initrd bytes are kept unchanged and followed by one small,
uncompressed, deterministic archive containing only the OREZ Plymouth theme
(two-step, a plugin the live initrd already ships) and plymouthd.conf.
"""
import hashlib
from pathlib import Path

MTIME = 1793923200


def _entry(name, mode, data=b''):
    name_b = name.encode() + b'\0'
    fields = [0, mode, 0, 0, 1, MTIME, len(data), 0, 0, 0, 0, len(name_b), 0]
    head = b'070701' + b''.join(b'%08X' % f for f in fields)
    pad = lambda n: b'\0' * ((4 - n % 4) % 4)
    return head + name_b + pad(len(head) + len(name_b)) + data + pad(len(data))


def archive(theme_dir):
    theme_dir = Path(theme_dir)
    out = []
    dirs = ['etc', 'etc/plymouth', 'usr', 'usr/share', 'usr/share/plymouth',
            'usr/share/plymouth/themes', 'usr/share/plymouth/themes/orez']
    out += [_entry(d, 0o040755) for d in dirs]
    out.append(_entry('etc/plymouth/plymouthd.conf', 0o100644, b'[Daemon]\nTheme=orez\n'))
    for f in sorted(theme_dir.iterdir()):
        if f.is_file():
            out.append(_entry('usr/share/plymouth/themes/orez/' + f.name, 0o100644, f.read_bytes()))
    out.append(_entry('TRAILER!!!', 0))
    data = b''.join(out)
    return data + b'\0' * ((512 - len(data) % 512) % 512)


def append(initrd, theme_dir):
    initrd = Path(initrd)
    extra = archive(theme_dir)
    before = initrd.read_bytes()
    initrd.write_bytes(before + extra)
    return {'base_initrd_sha256': hashlib.sha256(before).hexdigest(),
            'splash_archive_sha256': hashlib.sha256(extra).hexdigest(), 'splash_archive_bytes': len(extra)}
