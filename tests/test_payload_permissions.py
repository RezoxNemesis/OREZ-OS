"""Regression for ordinary users denied access by a restrictive build umask."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('orez_stage', ROOT / 'build/stage-overlay.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PayloadPermissionsTests(unittest.TestCase):
    def test_private_checkout_becomes_readable_without_mutating_sources_or_link_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / 'source'
            (src / 'usr/bin').mkdir(parents=True, mode=0o700)
            command = src / 'usr/bin/orezctl'
            command.write_text('#!/bin/sh\nexit 0\n')
            command.chmod(0o700)
            (src / 'etc').mkdir(mode=0o700)
            asset = src / 'etc/orez-release'
            asset.write_text('OREZ')
            asset.chmod(0o600)
            external = root / 'outside'
            external.write_text('do not chmod')
            external.chmod(0o600)
            (src / 'etc/link').symlink_to(external)
            output = root / 'output'
            module.stage(src, output)
            for item in [output, output / 'usr', output / 'usr/bin', output / 'etc']:
                self.assertEqual(item.stat().st_mode & 0o7777, 0o755)
            self.assertEqual((output / 'usr/bin/orezctl').stat().st_mode & 0o7777, 0o755)
            self.assertEqual((output / 'etc/orez-release').stat().st_mode & 0o7777, 0o644)
            self.assertEqual(command.stat().st_mode & 0o7777, 0o700)
            self.assertEqual(asset.stat().st_mode & 0o7777, 0o600)
            self.assertEqual(external.stat().st_mode & 0o7777, 0o600)
            self.assertTrue((output / 'etc/link').is_symlink())

    def test_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                module.stage(Path(temp), Path(temp))
