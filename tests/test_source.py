import os
import pathlib
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
OVERLAY = ROOT / 'overlay'


class OrezSourceTests(unittest.TestCase):
    def test_wallpaper_svg_parses(self):
        tree = ET.parse(OVERLAY / 'usr/share/backgrounds/orez/orez-ink.svg')
        self.assertEqual(tree.getroot().tag, '{http://www.w3.org/2000/svg}svg')

    def test_desktop_files_have_registered_commands(self):
        for path in OVERLAY.rglob('*.desktop'):
            txt = path.read_text()
            self.assertIn('[Desktop Entry]', txt)
            self.assertIn('Type=Application', txt)
            exec_line = next(line for line in txt.splitlines() if line.startswith('Exec='))[5:]
            if exec_line.startswith('/usr/bin/orez-'):
                self.assertTrue((OVERLAY / exec_line.split()[0].lstrip('/')).exists())

    def test_scripts_syntax(self):
        for script in [*ROOT.joinpath('build').glob('*.sh'), *OVERLAY.joinpath('usr/bin').iterdir()]:
            subprocess.run(['bash', '-n', str(script)], check=True)

    def test_overlay_is_unprivileged_and_visible(self):
        self.assertFalse(list(OVERLAY.rglob('*.service')))
        self.assertFalse(list(OVERLAY.rglob('sudoers*')))
        self.assertFalse(list(OVERLAY.rglob('*authorized_keys*')))
        first_login = (OVERLAY / 'etc/xdg/autostart/orez-initialize.desktop').read_text()
        self.assertIn('Exec=/usr/bin/orez-session-init', first_login)

    def test_status_does_not_require_root(self):
        p = subprocess.run([str(OVERLAY / 'usr/bin/orezctl'), 'status'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn('LIVE TEST ONLY', p.stdout)
        self.assertIn('NOT ENABLED', p.stdout)

    def test_orezctl_denies_unknown_commands(self):
        p = subprocess.run([str(OVERLAY / 'usr/bin/orezctl'), 'set-root-password'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_builder_has_no_raw_disk_writer(self):
        build = (ROOT / 'build/build-live.sh').read_text()
        for dangerous in ['mkfs.', 'wipefs', 'sgdisk', 'parted ', 'dd if=', 'sudo ']:
            self.assertNotIn(dangerous, build)
        self.assertIn('sha256sum -c', build)
        self.assertIn('gpgv', build)
        self.assertIn('-boot_image any replay', build)


if __name__ == '__main__':
    unittest.main(verbosity=2)
