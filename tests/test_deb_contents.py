import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "orez_deb_audit", ROOT / "build/verify-deb-files.py"
)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

LISTING = """drwxr-xr-x root/root         0 2026-11-05 00:00 ./
drwxr-xr-x root/root         0 2026-11-05 00:00 ./usr/
drwxr-xr-x root/root         0 2026-11-05 00:00 ./usr/bin/
-rwxr-xr-x root/root        45 2026-11-05 00:00 ./usr/bin/orezctl
"""


class DebAuditTests(unittest.TestCase):
    def test_exact_archive_payload_without_maintainer_scripts_passes_source_gate(self):
        result = audit.inspect(LISTING, "usr/bin/orezctl\n", ["./control"],
                               "orez-shell", "all")
        self.assertEqual(result["status"], "PACKAGE_CONTENTS_PASS")
        self.assertFalse(result["installation_approved"])

    def test_missing_extra_or_symlink_blocks(self):
        missing = audit.inspect(LISTING, "usr/bin/other\n", ["./control"],
                                "orez-shell", "all")
        self.assertEqual(missing["status"], "BLOCKED")
        self.assertIn("usr/bin/orezctl", missing["unexpected_files"])
        symlink_listing = LISTING + (
            "lrwxrwxrwx root/root 0 2026-11-05 00:00 ./usr/bin/other -> /bin/sh\n"
        )
        extra = audit.inspect(symlink_listing, "usr/bin/orezctl\n", ["./control"],
                              "orez-shell", "all")
        self.assertEqual(extra["status"], "BLOCKED")
        self.assertIn("usr/bin/other", extra["nonregular_payload_files"])

    def test_package_scripts_or_wrong_identity_blocks(self):
        for bad in (["./control", "./postinst"], ["./control", "./preinst"],
                    ["./control", "./random.conf"]):
            result = audit.inspect(LISTING, "usr/bin/orezctl\n", bad,
                                   "orez-shell", "all")
            self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(audit.inspect(LISTING, "usr/bin/orezctl\n",
                                       ["./control"], "wrong-name", "amd64")["status"],
                         "BLOCKED")

    def test_manifest_rejects_absolute_traversal_and_duplicates(self):
        for text in ("/etc/passwd\n", "../root\n", "a\na\n", ""):
            with self.subTest(value=text), self.assertRaises(ValueError):
                audit.manifest(text)

    def test_ci_invokes_pkg_audit_after_build(self):
        workflow = (ROOT / ".github/workflows/orez-live.yml").read_text()
        self.assertIn("python3 build/verify-deb-files.py", workflow)
        self.assertIn("bash build/package-shell.sh", workflow)
        self.assertLess(workflow.index("bash build/package-shell.sh"),
                        workflow.index("python3 build/verify-deb-files.py"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
