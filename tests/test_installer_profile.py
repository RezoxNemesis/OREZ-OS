"""Inactive installer configuration: stale sources fail before any output is written."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
spec = importlib.util.spec_from_file_location('installer_profile', ROOT / 'build/prepare-installer-profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class InstallerProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.name = 'etc/calamares/settings.conf'
        path = self.source / self.name
        path.parent.mkdir(parents=True)
        path.write_text('optional-network: true\n')
        self.status = self.root / 'status'
        self.status.write_text('Package: calamares\nStatus: install ok installed\nArchitecture: amd64\nVersion: 3.3.14\n\n')
        self.unpack = self.root / 'image/installer/orez-unpackfs-candidate.conf'
        self.unpack.parent.mkdir(parents=True)
        self.unpack.write_text('unpack: []\n')
        self.value = {
            'schema': 1, 'purpose': 'orez-inactive-installer-profile',
            'installation_approved': False, 'base_filesystem_sha256': 'a' * 64,
            'calamares_version': '3.3.14', 'required_installed_packages': {},
            'source_config_sha256': {self.name: profile.digest(path.read_bytes())},
            'changes': {self.name: {
                'replacements': [['optional-network: true\n', 'optional-network: false\n']],
                'expected_output_sha256': profile.digest(b'optional-network: false\n')}},
            'unpack_candidate_sha256': profile.digest(self.unpack.read_bytes()),
            'limitations': ['Fixture: no installation proof'],
        }
        self.path = self.root / 'profile.json'
        self.path.write_text(json.dumps(self.value))
        self.output = self.root / 'candidate'
        self.live = {'base_filesystem_sha256': 'a' * 64,
                     'base_status_sha256': profile.digest(self.status.read_bytes())}

    def prepare(self, output=None):
        with patch.object(profile, 'ROOT', self.root), patch.object(profile, 'live_profile', return_value=self.live):
            with contextlib.redirect_stdout(io.StringIO()):
                profile.prepare(self.source, self.status, output or self.output, self.path)

    def test_exact_source_renders_inactive_candidate_with_provenance(self):
        self.prepare()
        self.assertEqual((self.output / self.name).read_text(), 'optional-network: false\n')
        record = json.loads((self.output / 'profile-report.json').read_text())
        self.assertFalse(record['activated'])
        self.assertFalse(record['installation_approved'])
        self.assertEqual(record['profile_sha256'], profile.digest(self.path.read_bytes()))
        self.assertEqual(len(record['generated_config_sha256']), 2)
        self.assertEqual((self.source / self.name).read_text(), 'optional-network: true\n')

    def test_stale_source_status_and_unpack_refused_before_output(self):
        for path in [self.source / self.name, self.status, self.unpack]:
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b'changed\n')
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse(self.output.exists())
                path.write_bytes(original)

    def test_ambiguous_or_unreviewed_replacement_refused(self):
        for source, rules in [
            ('x x', {'replacements': [['x', 'y']], 'expected_output_sha256': '0' * 64}),
            ('x', {'replacements': [['z', 'y']], 'expected_output_sha256': '0' * 64}),
            ('x', {'replacements': [['x', 'y']], 'expected_output_sha256': '0' * 64}),
        ]:
            with self.subTest(source=source, rules=rules), self.assertRaises(ValueError):
                profile.render(source, rules)

    def test_existing_or_aliased_destination_refused(self):
        existing = self.root / 'existing'
        existing.mkdir()
        (existing / 'keep').write_text('preserve')
        link = self.root / 'alias'
        link.symlink_to(existing, target_is_directory=True)
        for output in [existing, link / 'nested']:
            with self.subTest(output=output), self.assertRaises(ValueError):
                self.prepare(output)
        self.assertEqual((existing / 'keep').read_text(), 'preserve')
        self.assertFalse((existing / 'nested').exists())

    def test_source_escape_and_symlink_refused(self):
        path = self.source / self.name
        path.unlink()
        outside = self.root / 'outside'
        outside.write_text('optional-network: true\n')
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Unsafe installer source path'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_system_destination_with_dotdot_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'system configuration destination'):
            self.prepare(Path('/tmp/../etc/orez-inactive-installer-test'))

    def test_claimed_approval_and_wrong_bootloader_version_refused(self):
        for field, value in [('installation_approved', True),
                             ('required_installed_packages', {'shim-signed': 'missing'})]:
            with self.subTest(field=field):
                changed = {**self.value, field: value}
                self.path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse(self.output.exists())
