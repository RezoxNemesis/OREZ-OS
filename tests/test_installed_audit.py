import importlib.util
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("orez_installed_audit", HERE / 'build/audit-installed-root.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class InstallerAuditTests(unittest.TestCase):
    def fixture(self, root, present=True, unsafe_override=False, crypto='luks', btrfs=True):
        def write(path, content):
            p = root / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        if present:
            write('etc/orez-release', 'NAME=OREZ OS\n')
            write('usr/bin/orezctl', '#!/bin/bash\n')
        write('usr/lib/sysctl.d/10-apparmor.conf', 'kernel.apparmor_restrict_unprivileged_userns = 1\n')
        if unsafe_override:
            write('etc/sysctl.d/20-apparmor.conf', 'kernel.apparmor_restrict_unprivileged_userns = 0\n')
        if crypto:
            write('etc/crypttab', f'luks-root UUID=deadbeef none {crypto}\n')
        if btrfs:
            write('etc/fstab', 'UUID=foo / btrfs defaults,subvol=@ 0 0\n')
        else:
            write('etc/fstab', 'UUID=foo / ext4 defaults 0 1\n')

    def test_safe_static_fixtures_do_not_claim_install_safety(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); self.fixture(root)
            result=mod.inspect(root,True,True)
            self.assertEqual(result['status'],'static-checks-passed')
            self.assertFalse(result['safe_to_install'])

    def test_missing_orez_identity_is_install_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); self.fixture(root,present=False)
            result=mod.inspect(root)
            self.assertIn('installed_orez_identity',result['blockers'])

    def test_kubuntu_live_only_apparmor_policy_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); self.fixture(root,unsafe_override=True)
            result=mod.inspect(root)
            self.assertIn('apparmor_live_override',result['blockers'])

    def test_luks_crypttab_without_luks_option_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); self.fixture(root,crypto='defaults')
            result=mod.inspect(root,True)
            self.assertIn('luks_root_crypttab',result['blockers'])

    def test_missing_crypttab_blocks_when_encryption_expected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); self.fixture(root,crypto='')
            result=mod.inspect(root,True)
            self.assertIn('luks_root_crypttab',result['blockers'])

    def test_non_btrfs_root_blocks_when_btrfs_expected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp); self.fixture(root,btrfs=False)
            result=mod.inspect(root,False,True)
            self.assertIn('btrfs_root',result['blockers'])

    def test_symlink_outside_installed_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)/'disk'; root.mkdir()
            (root/'etc').symlink_to('/etc')
            with self.assertRaises(ValueError):
                mod.inspect(root)

if __name__=='__main__':
    unittest.main()
