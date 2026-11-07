"""Source-level acceptance checks for the searchable OREZ Settings front door."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "overlay"


class SettingsUiTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((OVERLAY / "usr/share/orez/settings-catalog.json").read_text())

    def test_catalog_has_plain_language_categories_and_search_synonyms(self):
        self.assertEqual(self.catalog["schema"], 1)
        categories = {item["title"]: item for item in self.catalog["categories"]}
        for name in ["Personalisation", "Display and sound", "Network and devices",
                     "Apps and files", "Updates and recovery", "System and advanced tools"]:
            self.assertIn(name, categories)
        all_text = json.dumps(self.catalog).casefold()
        for word in ["wi-fi", "bluetooth", "display", "password", "backup",
                     "recovery", "terminal", "developer", "usb"]:
            self.assertIn(word, all_text)

    def test_every_catalog_action_is_allowlisted_and_explained(self):
        allowed = {"system-settings", "network", "bluetooth", "power",
                   "files", "apps", "connect", "help", "appearance"}
        for category in self.catalog["categories"]:
            self.assertTrue(category["title"])
            for item in category["items"]:
                self.assertIn(item["action"], allowed)
                self.assertTrue(item["title"])
                self.assertTrue(item["description"])
                self.assertTrue(item["keywords"])

    def test_ui_uses_no_shell_or_privileged_command(self):
        source = (OVERLAY / "usr/lib/orez/settings_ui.py").read_text()
        ast.parse(source)
        self.assertIn("subprocess.Popen(command, close_fds=True)", source)
        self.assertNotIn("shell=True", source)
        for prohibited in ["sudo ", "pkexec", "os.system(", "eval(",
                           "mkfs", "wipefs", "parted "]:
            self.assertNotIn(prohibited, source)

    def test_existing_settings_launcher_opens_the_native_hub(self):
        launcher = (OVERLAY / "usr/bin/orez-settings").read_text()
        self.assertIn("/usr/lib/orez/settings_ui.py", launcher)
        self.assertIn('exec python3', launcher)
        desktop = (OVERLAY / "usr/share/applications/orez-settings.desktop").read_text()
        self.assertIn("Exec=/usr/bin/orez-settings", desktop)
        manifest = (ROOT / "image/installer/installed-files.txt").read_text()
        for path in ["usr/lib/orez/settings_ui.py", "usr/share/orez/settings-catalog.json"]:
            self.assertIn(path, manifest)

    def test_recovery_copy_does_not_claim_unimplemented_recovery(self):
        item = next(x for c in self.catalog["categories"] for x in c["items"]
                    if x["title"] == "Help and recovery")
        self.assertIn("not enabled", item["description"].lower())
        self.assertEqual(item["action"], "help")


if __name__ == "__main__":
    unittest.main(verbosity=2)
