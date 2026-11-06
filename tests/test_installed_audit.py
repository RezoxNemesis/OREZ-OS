import importlib.util
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("orez_installed_audit", HERE / 'build/audit-installed-root.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class InstallerAuditTests(unittest.TestCase):
    def owner_fixture(self, root):
        self.fixture(root)
        for path, value in {
            'etc/passwd': 'root:x:0:0:root:/root:/bin/bash\nowner:x:1000:1000:Owner:/home/owner:/bin/bash\n',
            'etc/shadow': 'root:!:20000:0:99999:7:::\nowner:$y$fixture$not-a-real-credential:20000:0:99999:7:::\n',
            'etc/group': 'root:x:0:\nowner:x:1000:\nsudo:x:27:owner\n',
            'etc/sudoers': 'root ALL=(ALL:ALL) ALL\n%sudo ALL=(ALL:ALL) ALL\n',
        }.items():
            (root / path).write_text(value)
        (root / 'etc/shadow').chmod(0o600)

    def test_owner_static_policy_does_not_claim_runtime_or_install_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp); self.owner_fixture(root)
            result = mod.inspect(root, owner='owner')
            self.assertEqual(result['blockers'], [])
            self.assertFalse(result['safe_to_install'])
            self.assertNotIn('not-a-real-credential', str(result))

    def test_unlocked_root_blank_owner_and_readable_shadow_block(self):
        for text, mode, expected in [
            ('root:$6$salt$fake:20000:0:99999:7:::\nowner:$y$salt$fake:20000:0:99999:7:::\n', 0o600, 'root_password_locked'),
            ('root:!:20000:0:99999:7:::\nowner::20000:0:99999:7:::\n', 0o600, 'owner_password'),
            ('root:!:20000:0:99999:7:::\nowner:$:20000:0:99999:7:::\n', 0o600, 'owner_password'),
            ('root:!:20000:0:99999:7:::\nowner:$y$salt$fake:20000:0:99999:7:::\n', 0o644, 'shadow_permissions'),
        ]:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp); self.owner_fixture(root)
                (root / 'etc/shadow').write_text(text); (root / 'etc/shadow').chmod(mode)
                self.assertIn(expected, mod.inspect(root, owner='owner')['blockers'])

    def test_alias_uid_and_other_primary_administrator_group_block(self):
        for extra, expected in [
            ('alias:x:01000:1001:Alias:/home/alias:/bin/bash\n', 'owner_identity'),
            ('other:x:1001:027:Other:/home/other:/bin/bash\n', 'administrator_groups'),
            ('backdoor:x:00:1002:Other:/home/backdoor:/bin/bash\n', 'root_identity'),
        ]:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp); self.owner_fixture(root)
                with (root / 'etc/passwd').open('a') as stream: stream.write(extra)
                self.assertIn(expected, mod.inspect(root, owner='owner')['blockers'])

    def test_extra_sudo_group_member_and_passwordless_rule_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp); self.owner_fixture(root)
            (root / 'etc/group').write_text('sudo:x:27:owner,stranger\n')
            directory = root / 'etc/sudoers.d'; directory.mkdir()
            (directory / 'unsafe').write_text('%sudo ALL=(ALL:ALL) NOPASSWD: ALL\n')
            result = mod.inspect(root, owner='owner')
            self.assertIn('administrator_groups', result['blockers'])
            self.assertIn('known_passwordless_sudo', result['blockers'])

    def test_external_sudo_include_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp); self.owner_fixture(root)
            (root / 'etc/sudoers.d').symlink_to('/etc')
            with self.assertRaisesRegex(ValueError, 'escapes'):
                mod.inspect(root, owner='owner')

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
