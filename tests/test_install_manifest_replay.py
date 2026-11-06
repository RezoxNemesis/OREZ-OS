"""Read-only, synthetic Calamares payload rehearsal.

Uses only a TemporaryDirectory on the CI runner. No block devices, mounting,
Calamares execution, firmware or privilege escalation. Passing is NOT an
installation/boot/security certification.
"""
import importlib.util
import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "overlay"
MANIFEST = ROOT / "image/installer/installed-files.txt"
PROFILE = ROOT / "image/installer/orez-unpackfs-candidate.conf"
AUDIT = ROOT / "build/audit-installed-root.py"

spec = importlib.util.spec_from_file_location("orez_installed_audit_synthetic", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SyntheticInstallPayloadTests(unittest.TestCase):
    def entries(self):
        raw = MANIFEST.read_text().splitlines()
        return [line.strip() for line in raw if line.strip() and not line.lstrip().startswith("#")]

    def test_inactive_profile_matches_exact_three_ordered_sources(self):
        actual = [
            line.rstrip()
            for line in PROFILE.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        expected = [
            "---",
            "unpack:",
            '  - source: "/cdrom/casper/filesystem.squashfs"',
            '    sourcefs: "squashfs"',
            '    destination: ""',
            "    exclude:",
            '      - "etc/sysctl.d/20-apparmor.conf"',
            '  - source: "/cdrom/casper/orez-apps.squashfs"',
            '    sourcefs: "squashfs"',
            '    destination: ""',
            '  - source: "/cdrom/casper/orez-install.squashfs"',
            '    sourcefs: "squashfs"',
            '    destination: ""',
        ]
        self.assertEqual(actual, expected)
        self.assertFalse((OVERLAY / "etc/calamares/modules/unpackfs.conf").exists())
        self.assertTrue((OVERLAY / "usr/bin/calamares").exists())

    def test_install_manifest_is_allowlisted_and_unprivileged(self):
        entries = self.entries()
        self.assertGreaterEqual(len(entries), 12)
        self.assertEqual(len(entries), len(set(entries)))
        for relative in entries:
            self.assertFalse(relative.startswith("/"), relative)
            self.assertNotIn("..", pathlib.PurePosixPath(relative).parts)
            file = OVERLAY / relative
            self.assertTrue(file.is_file(), relative)
            self.assertFalse(file.is_symlink(), relative)
        for forbidden in [
            "usr/bin/calamares",
            "usr/bin/orez-gui-verify",
            "usr/bin/orez-live-verify",
            "etc/xdg/plasma-workspace/env/90-orez-vm-software.sh",
            "etc/sysctl.d/20-apparmor.conf",
        ]:
            self.assertNotIn(forbidden, entries)

    def test_synthetic_root_replay_and_negative_apparmor_regression(self):
        with tempfile.TemporaryDirectory(prefix="orez-synthetic-root-") as temporary:
            root = pathlib.Path(temporary) / "root"
            root.mkdir()

            # Synthetic vendor baseline. This is NOT extracted from real Kubuntu.
            vendor = root / "usr/lib/sysctl.d/10-apparmor.conf"
            vendor.parent.mkdir(parents=True)
            vendor.write_text("kernel.apparmor_restrict_unprivileged_userns = 1\n")

            # Illustrate the real upstream live-only policy leak as a regression.
            live_override = root / "etc/sysctl.d/20-apparmor.conf"
            live_override.parent.mkdir(parents=True)
            live_override.write_text("kernel.apparmor_restrict_unprivileged_userns = 0\n")
            unsafe = audit.inspect(root)
            self.assertIn("apparmor_live_override", unsafe["blockers"])
            self.assertIn("installed_orez_identity", unsafe["blockers"])

            # Replay only the candidate's declared exclusion and the genuine
            # repository allowlist into a disposable directory.
            live_override.unlink()
            for relative in self.entries():
                source = OVERLAY / relative
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target, follow_symlinks=False)

            result = audit.inspect(root)
            self.assertEqual(result["status"], "static-checks-passed")
            self.assertFalse(result["safe_to_install"])
            self.assertEqual(result["blockers"], [])
            self.assertFalse((root / "usr/bin/calamares").exists())
            self.assertFalse((root / "usr/lib/systemd/system/orez-gui-verify.service").exists())
            self.assertFalse((root / "etc/xdg/plasma-workspace/env/90-orez-vm-software.sh").exists())
            self.assertFalse(live_override.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
