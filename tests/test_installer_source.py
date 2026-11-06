"""Source-inspection regressions; these never execute an installer."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
spec = importlib.util.spec_from_file_location('installer_source', ROOT / 'build/inspect-installer-source.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class InstallerSourceTests(unittest.TestCase):
    def configs(self, names=None):
        values = {p: '' for p in audit.CONFIGS}
        names = names or ['filesystem', 'orez-apps', 'orez-install']
        values[audit.CONFIGS[1]] = 'unpack:\n' + ''.join(
            '  - source: "/cdrom/casper/' + name + '.squashfs"\n' for name in names)
        return values

    def test_correct_source_order_does_not_approve_installation(self):
        r = audit.assess(self.configs(), True)
        self.assertEqual(r['configuration_blockers'], [])
        self.assertTrue(r['runtime_gates'])
        self.assertFalse(r['installation_approved'])
        self.assertFalse(r['release_approved'])

    def test_stock_reordered_and_live_only_sources_remain_blocked(self):
        for names in [['filesystem'], ['filesystem', 'orez-install', 'orez-apps'],
                      ['filesystem', 'orez-apps', 'orez-install', 'zz-orez']]:
            with self.subTest(names=names):
                r = audit.assess(self.configs(names), True)
                self.assertIn('active_unpack_sources_do_not_match_integrated_layers', r['configuration_blockers'])

    def test_apparmor_override_guard_and_missing_users_reported(self):
        c = self.configs()
        c[audit.CONFIGS[-1]] = 'kernel.apparmor_restrict_unprivileged_userns = 0 # live only\n'
        del c['etc/calamares/modules/users.conf']
        r = audit.assess(c, False)
        self.assertEqual(len(r['configuration_blockers']), 3)
        self.assertIn('etc/calamares/modules/users.conf', r['missing_configuration'])

    def test_wrong_digest_refuses_before_external_commands_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / 'input.iso'; iso.write_bytes(b'fixture')
            output = Path(directory) / 'output'
            with patch.object(audit.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                    audit.inspect(iso, '0' * 64, output)
                run.assert_not_called()
            self.assertFalse(output.exists())

    def test_device_and_symlink_inputs_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / 'link'; link.symlink_to('/dev/null')
            for path in [link, Path('/dev/null')]:
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'regular ISO'):
                    audit.inspect(path, '0' * 64, Path(directory) / 'output')
