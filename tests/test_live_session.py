"""The live login must reach Plasma without an inherited installer-prompt gate."""
import configparser
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / 'image/live-owner/usr/lib/orez/orez-session-trace'


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
            '/bin/sh', '/usr/lib/orez/orez-session-trace'])
        self.assertEqual(value['TryExec'], '/usr/bin/startplasma-wayland')
        self.assertEqual(value['DesktopNames'], 'KDE')
        self.assertFalse(config['Autologin']['User'])
        self.assertEqual(config['Autologin']['Relogin'], 'false')

    def test_live_entry_is_not_in_normal_install_payload(self):
        manifest = (ROOT / 'image/installer/installed-files.txt').read_text()
        self.assertNotIn('usr/share/orez/wayland-sessions/orez.desktop', manifest)
        self.assertNotIn('usr/lib/orez/orez-session-trace', manifest)
        self.assertFalse((ROOT / 'overlay/usr/share/orez/wayland-sessions/orez.desktop').exists())

    def test_trace_wrapper_preserves_exact_session_and_exit_status(self):
        wrapper = TRACE.read_text()
        self.assertIn('/usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland', wrapper)
        self.assertIn('status=$?', wrapper)
        self.assertIn('exit "$status"', wrapper)
        self.assertIn('plasma_session_child_exit=$status', wrapper)
        self.assertNotIn('exec startplasma', wrapper)
        self.assertNotIn('sudo ', wrapper)
        self.assertNotIn('setenforce', wrapper)
        self.assertNotIn('env >', wrapper)
        self.assertNotIn('printenv', wrapper)
        self.assertIn('DBUS_SESSION_BUS_ADDRESS', wrapper)
        self.assertNotIn('DBUS_SESSION_BUS_ADDRESS=', wrapper)
        subprocess.run(['/bin/sh', '-n', str(TRACE)], check=True)

    def test_trace_wrapper_logs_child_status_without_dumping_environment(self):
        with tempfile.TemporaryDirectory(prefix='orez-session-trace-test-') as directory:
            root = Path(directory)
            helper = root / 'plasma-helper'
            logger = root / 'logger'
            log_file = root / 'journal-lines.txt'
            test_wrapper = root / 'trace-wrapper'
            logger.write_text('#!/bin/sh\nprintf \'%s\\n\' "$*" >> ' + shlex.quote(str(log_file)) + '\n')
            logger.chmod(0o755)
            template = TRACE.read_text()
            template = template.replace('/usr/bin/logger', str(logger))
            template = template.replace(
                '/usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed',
                str(helper))
            test_wrapper.write_text(template)

            for expected in (0, 64):
                helper.write_text('#!/bin/sh\nexit ' + str(expected) + '\n')
                helper.chmod(0o755)
                env = {
                    'PATH': '/usr/bin:/bin',
                    'HOME': str(root),
                    'XDG_RUNTIME_DIR': str(root),
                    'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/tmp/orez-test-bus',
                    'XDG_SESSION_TYPE': 'wayland',
                    'OREZ_TEST_SECRET': 'must-not-appear-in-trace',
                }
                result = subprocess.run(
                    ['/bin/sh', str(test_wrapper)],
                    env=env, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, expected)
                lines = log_file.read_text()
                self.assertIn('wrapper_started uid=', lines)
                self.assertIn('plasma_session_child_exit=' + str(expected), lines)
                self.assertNotIn('must-not-appear-in-trace', lines)
                log_file.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
