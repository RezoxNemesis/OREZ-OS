"""Pure source tests for read-only OREZ installer payload path collision detection."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "orez_collision_check", ROOT / "build/check-install-collisions.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def listing(*paths):
    return "squashfs-root\n" + "\n".join(f"squashfs-root/{p}" for p in paths)


class InstallCollisionTests(unittest.TestCase):
    def test_files_do_not_overwrite_original_kubuntu(self):
        base = listing("etc", "etc/passwd", "usr", "usr/bin", "usr/bin/bash")
        payload = listing("usr", "usr/bin", "usr/bin/orezctl", "etc", "etc/orez-release")
        result = module.inspect(base, payload, "usr/bin/orezctl\netc/orez-release\n")
        self.assertEqual(result["status"], "STATIC_FILE_PATHS_PASS")
        self.assertFalse(result["installation_approved"])

    def test_existing_base_file_name_blocks(self):
        base = listing("usr", "usr/bin", "usr/bin/orezctl")
        payload = listing("usr", "usr/bin", "usr/bin/orezctl")
        result = module.inspect(base, payload, "usr/bin/orezctl\n")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["overwrites_existing_base_paths"], ["usr/bin/orezctl"])

    def test_missing_or_unexpected_payload_path_blocks(self):
        base = listing("usr", "usr/bin")
        payload = listing("usr", "usr/bin", "usr/bin/extra")
        result = module.inspect(base, payload, "usr/bin/orezctl\n")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("usr/bin/orezctl", result["missing_manifest_paths"])
        self.assertIn("usr/bin/extra", result["unexpected_payload_paths"])

    def test_extra_directories_allowed_but_extra_files_not_allowed(self):
        base = listing("usr", "usr/bin")
        payload = listing("usr", "usr/bin", "usr/bin/orezctl", "usr/share", "usr/share/unused")
        result = module.inspect(base, payload, "usr/bin/orezctl\n")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("usr/share/unused", result["unexpected_payload_paths"])

    def test_bad_or_duplicate_manifest_blocks(self):
        for value in ("/etc/passwd\n", "../outside\n", "etc/a\netc/a\n", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.manifest_paths(value)

    def test_real_allowlist_is_valid_and_still_not_installer_certification(self):
        content = (ROOT / "image/installer/installed-files.txt").read_text()
        names = module.manifest_paths(content)
        self.assertGreaterEqual(len(names), 12)
        self.assertNotIn("usr/bin/calamares", names)
        self.assertNotIn("etc/sysctl.d/20-apparmor.conf", names)
        self.assertNotIn("etc/xdg/plasma-workspace/env/90-orez-vm-software.sh", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
