"""Regression checks for the OREZ Help & Recovery front door."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "overlay"


class HelpRecoveryTests(unittest.TestCase):
    def test_python_source_parses_and_has_read_only_diagnostics(self):
        source = (OVERLAY / "usr/lib/orez/help_recovery_ui.py").read_text()
        ast.parse(source)
        self.assertIn('subprocess.run(args, capture_output=True, text=True, timeout=timeout', source)
        self.assertIn('"systemctl", "--failed"', source)
        self.assertIn('shutil.disk_usage("/")', source)
        for prohibited in ["shell=True", "sudo ", "pkexec", "os.system(", "mkfs",
                           "wipefs", "parted ", "chpasswd", "mount -o", "rm -rf"]:
            self.assertNotIn(prohibited, source)

    def test_ui_is_explicit_about_unavailable_recovery_and_installation(self):
        source = (OVERLAY / "usr/lib/orez/help_recovery_ui.py").read_text()
        for claim in ["NOT AVAILABLE", "DISABLED", "No qualified restore-point workflow",
                      "No backup is created or restored", "never formats, partitions"]:
            self.assertIn(claim, source)

    def test_diagnostic_export_is_user_chosen_and_minimizes_private_data(self):
        source = (OVERLAY / "usr/lib/orez/help_recovery_ui.py").read_text()
        self.assertIn("QFileDialog.getSaveFileName", source)
        self.assertIn("No username, serial number, IP address", source)
        self.assertNotIn("journalctl", source)
        self.assertNotIn("nmcli", source)

    def test_help_launcher_and_desktop_entry_are_registered(self):
        launcher = (OVERLAY / "usr/bin/orez-help").read_text()
        self.assertIn("/usr/lib/orez/help_recovery_ui.py", launcher)
        desktop = (OVERLAY / "usr/share/applications/orez-help.desktop").read_text()
        self.assertIn("Exec=/usr/bin/orez-help", desktop)
        manifest = (ROOT / "image/installer/installed-files.txt").read_text()
        for path in ["usr/bin/orez-help", "usr/share/applications/orez-help.desktop",
                     "usr/lib/orez/help_recovery_ui.py"]:
            self.assertIn(path, manifest)

    def test_settings_help_button_opens_dedicated_help_application(self):
        source = (OVERLAY / "usr/lib/orez/settings_ui.py").read_text()
        self.assertIn('"help": ["orez-help"]', source)
        self.assertNotIn('"help": ["xdg-open"', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
