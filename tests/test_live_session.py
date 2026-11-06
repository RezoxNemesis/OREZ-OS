"""The live login must reach Plasma without an inherited installer-prompt gate."""
import configparser
from pathlib import Path
import shlex
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LiveSessionTests(unittest.TestCase):
    def test_live_session_directory_resolves_to_direct_native_desktop(self):
        hook = (ROOT / 'image/initramfs/scripts/casper-bottom/15autologin').read_text()
        config = configparser.ConfigParser()
        config.read_string(hook.split("<<'EOF'\n", 1)[1].split('\nEOF', 1)[0])
        directory = ROOT / 'image/live-owner' / config['Wayland']['SessionDir'].lstrip('/')
        entries = list(directory.glob('*.desktop'))
        self.assertEqual(len(entries), 1)
        desktop = configparser.ConfigParser()
        desktop.read(entries[0])
        value = desktop['Desktop Entry']
        self.assertEqual(value['Name'], 'OREZ Desktop')
        self.assertEqual(shlex.split(value['Exec']), [
            '/usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed',
            '/usr/bin/startplasma-wayland'])
        self.assertEqual(value['TryExec'], '/usr/bin/startplasma-wayland')
        self.assertEqual(value['DesktopNames'], 'KDE')
        self.assertFalse(config['Autologin']['User'])
        self.assertEqual(config['Autologin']['Relogin'], 'false')

    def test_live_entry_is_not_in_normal_install_payload(self):
        manifest = (ROOT / 'image/installer/installed-files.txt').read_text()
        self.assertNotIn('usr/share/orez/wayland-sessions/orez.desktop', manifest)
        self.assertFalse((ROOT / 'overlay/usr/share/orez/wayland-sessions/orez.desktop').exists())
