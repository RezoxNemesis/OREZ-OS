"""Assembly boundaries: no wrong-base mixing or silently skipped owner setup."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
import live_assembly as assembly
spec = importlib.util.spec_from_file_location('components', ROOT / 'build/install-orez-layer.py')
components = importlib.util.module_from_spec(spec)
spec.loader.exec_module(components)

MENU = '''set timeout=30
menuentry "Try or Install Kubuntu" {
    linux  /casper/vmlinuz  --- quiet splash
    initrd /casper/initrd
}
menuentry "Kubuntu (safe graphics)" {
    linux /casper/vmlinuz nomodeset --- quiet splash
    initrd /casper/initrd
}
menuentry "OEM install (for manufacturers)" {
    linux /casper/vmlinuz only-ubiquity
    initrd /casper/initrd
}
'''


class LiveAssemblyTests(unittest.TestCase):
    def test_both_uefi_choices_run_owner_enrollment_and_preserve_safe_graphics(self):
        result = assembly.brand_grub(MENU)
        kernels = [line.split() for line in result.splitlines() if line.strip().startswith('linux ')]
        self.assertEqual(len(kernels), 2)
        self.assertTrue(all(line.count('boot=casper') == 1 for line in kernels))
        self.assertIn('nomodeset', kernels[1])
        self.assertNotIn('OEM install', result)
        self.assertNotIn('only-ubiquity', result)
        self.assertIn('Try OREZ OS (installation unavailable)', result)

    def test_changed_upstream_menu_requires_review(self):
        for menu in [MENU.replace('Try or Install Kubuntu', 'Install New OS'),
                     MENU.replace('OEM install (for manufacturers)', 'OEM wizard'),
                     MENU + '\nlinux /casper/vmlinuz\n',
                     MENU + '\nset layerfs-path=some-other-root\n']:
            with self.subTest(menu=menu), self.assertRaises(ValueError):
                assembly.brand_grub(menu)

    def test_contiguous_large_iso_extents_are_read_as_one_verified_filesystem(self):
        listing = "File data lba: 0 , 10 , 2 , 6000 , '/casper/filesystem.squashfs'\nFile data lba: 1 , 12 , 1 , 6000 , '/casper/filesystem.squashfs'\n"
        with patch.object(assembly.subprocess, 'check_output', return_value=listing):
            self.assertEqual(assembly.extent('input.iso', '/casper/filesystem.squashfs'), (20480, 6000))

    def test_invalid_extent_index_gap_and_length_fail(self):
        for second, size in [(13, 6000), (12, 7000), (12, 4096)]:
            text = f"File data lba: 0 , 10 , 2 , {size} , '/root'\nFile data lba: 1 , {second} , 1 , {size} , '/root'\n"
            with patch.object(assembly.subprocess, 'check_output', return_value=text), self.assertRaises(ValueError):
                assembly.extent('input.iso', '/root')
        with patch.object(assembly.subprocess, 'check_output', return_value="File data lba: 1 , 10 , 1 , 100 , '/root'\n"), self.assertRaises(ValueError):
            assembly.extent('input.iso', '/root')

    def test_truncated_extent_cannot_hash_as_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'iso'; source.write_bytes(b'prefixactual')
            import hashlib
            self.assertEqual(assembly.digest_range(source, 6, 6), hashlib.sha256(b'actual').hexdigest())
            with self.assertRaises(ValueError):
                assembly.digest_range(source, 6, 7)

    def test_development_parent_is_not_accepted_as_official(self):
        profile = assembly.profile()
        with patch.object(assembly, 'sha', return_value=profile['development_parent_sha256']), self.assertRaisesRegex(ValueError, 'Unrecognized parent'):
            assembly.verify_base(Path('/nonexistent-fixture.iso'))

    def test_wrong_apps_or_component_provenance_cannot_proceed(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / 'report.json'; report.write_text('{}')
            with patch.object(assembly, 'sha', return_value='wrong'), self.assertRaisesRegex(ValueError, 'Unreviewed application'):
                assembly.verify_components('apps', 'components', report)
            # An authentic app artifact alone does not authenticate a supplied
            # component layer or a manifest claiming to describe it.
            profile = assembly.profile()
            with patch.object(assembly, 'sha', return_value=profile['app_layer_sha256']), patch.object(assembly, 'squash_cat', return_value=b'tampered status'), self.assertRaisesRegex(ValueError, 'Application status'):
                assembly.verify_components('apps', 'components', report)

    def test_duplicate_package_records_are_rejected(self):
        record = 'Package: demo\nArchitecture: all\nStatus: install ok installed\nVersion: 1'
        self.assertEqual(assembly.blocks(record), {'demo:all': record})
        for text in [record + '\n\n' + record, 'Package: demo\nVersion: 1']:
            with self.assertRaises(ValueError):
                assembly.blocks(text)

    def test_component_delta_rejects_privilege_policy_and_deletion(self):
        file = {'type': 'file', 'mode': 0o644, 'uid': 0, 'gid': 0, 'xattrs': {}}
        with self.assertRaises(ValueError):
            components.allowed_changes({'usr/bin/orez-test': file}, {}, {'usr/bin/orez-test'})
        for name, item in [('etc/sudoers', file),
                           ('usr/bin/orez-test', dict(file, mode=0o4755)),
                           ('usr/bin/orez-test', dict(file, xattrs={'security.capability': 'opaque'}))]:
            with self.subTest(name=name, item=item), self.assertRaises(ValueError):
                components.allowed_changes({}, {name: item}, {'usr/bin/orez-test'})
        with self.assertRaises(ValueError):
            components.allowed_changes({'usr/bin/orez-test': file}, {'usr/bin/orez-test': dict(file, type='link')}, {'usr/bin/orez-test'})


if __name__ == '__main__':
    unittest.main()
