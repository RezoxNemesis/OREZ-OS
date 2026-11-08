import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('update_apply', ROOT / 'overlay/usr/lib/orez/update_apply.py')
up = importlib.util.module_from_spec(spec)
spec.loader.exec_module(up)

MANIFEST = {'schema': 1, 'version': '0.2', 'from_versions': ['0.1'], 'suites': ['resolute', 'resolute-updates'],
            'components': ['main', 'universe'], 'packages': ['wine', 'wine32:i386', 'lutris'],
            'steam_packages': ['steam-installer'], 'nvidia_packages': ['nvidia-driver-615-open'],
            'summary': ['Steam'], 'orez_shell': 'orez-shell_0.2.0-1_all.deb'}


def make_media(root: Path, files: dict[str, bytes]) -> Path:
    media = root / 'usb' / 'orez-update'
    media.mkdir(parents=True)
    lines = []
    for name, data in files.items():
        p = media / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        lines.append(hashlib.sha256(data).hexdigest() + '  ' + name)
    (media / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')
    return media


class UpdateTests(unittest.TestCase):
    def test_manifest_validation(self):
        self.assertEqual(up.load_manifest(json.dumps(MANIFEST))['version'], '0.2')
        for bad in ({**MANIFEST, 'schema': 2}, {**MANIFEST, 'packages': ['wine; rm -rf /']},
                    {**MANIFEST, 'suites': ['../x']}, {**MANIFEST, 'orez_shell': '../../evil.deb'},
                    {k: v for k, v in MANIFEST.items() if k != 'summary'}):
            with self.assertRaises(up.UpdateError):
                up.load_manifest(json.dumps(bad))

    def test_sums_reject_unsafe_paths(self):
        h = '0' * 64
        for bad in (f'{h}  ../etc/passwd', f'{h}  /etc/shadow', f'{h}  a b', 'nothex  update.json',
                    f'{h}  update.json\n{h}  update.json'):
            with self.assertRaises(up.UpdateError):
                up.parse_sums(bad)
        with self.assertRaises(up.UpdateError):  # update.json must be covered
            up.parse_sums(f'{h}  mirror/x.deb')
        self.assertIn('mirror/pool/a.deb', up.parse_sums(f'{h}  update.json\n{h} *mirror/pool/a.deb'))

    def test_copy_verifies_every_file_and_ignores_unlisted(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            media = make_media(t, {'update.json': json.dumps(MANIFEST).encode(), 'mirror/pool/a.deb': b'deb'})
            (media / 'extra-not-listed.sh').write_text('evil')
            up.LOG = t / 'log'
            up.copy_verified(media, t / 'dest')
            self.assertEqual((t / 'dest/mirror/pool/a.deb').read_bytes(), b'deb')
            self.assertFalse((t / 'dest/extra-not-listed.sh').exists())
            (media / 'mirror/pool/a.deb').write_bytes(b'tampered')
            with self.assertRaisesRegex(up.UpdateError, 'checksum'):
                up.copy_verified(media, t / 'dest2')

    def test_symlinked_payload_is_refused(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            media = make_media(t, {'update.json': b'{}', 'x': b'1'})
            (media / 'x').unlink(); (media / 'x').symlink_to('/etc/hostname')
            up.LOG = t / 'log'
            with self.assertRaises(up.UpdateError):
                up.copy_verified(media, t / 'dest')

    def test_find_media(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            media = make_media(t, {'update.json': b'{}'})
            self.assertEqual(up.find_media([media.parent, t / 'none']), [media])

    def test_plan_safety(self):
        up.plan_is_safe('Inst wine (10.0)\nInst nvidia-driver-615-open (615)\n')
        with self.assertRaises(up.UpdateError):
            up.plan_is_safe('Inst nvidia-dkms-615 (615)\n')
        with self.assertRaises(up.UpdateError):
            up.plan_is_safe('Remv orez-shell [0.1.0-4]\n')

    def test_sources_use_only_usb_unless_online(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 's'
            up.write_sources(p, Path('/var/cache/x/mirror'), MANIFEST, False)
            text = p.read_text()
            self.assertNotIn('http', text)
            self.assertIn('signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg', text)
            up.write_sources(p, Path('/m'), MANIFEST, True)
            self.assertIn('http://archive.ubuntu.com/ubuntu resolute ', p.read_text())

    def test_no_listener_or_background_service(self):
        src = (ROOT / 'overlay/usr/lib/orez/update_apply.py').read_text()
        for bad in ('socket', 'systemctl enable', 'autostart', 'curl', 'wget'):
            self.assertNotIn(bad, src)
        ui = (ROOT / 'overlay/usr/lib/orez/update_ui.py').read_text()
        self.assertIn("'pkexec'", ui)
        self.assertNotIn('sudo', ui)


if __name__ == '__main__':
    unittest.main()
