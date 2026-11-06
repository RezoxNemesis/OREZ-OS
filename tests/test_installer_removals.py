import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
spec = importlib.util.spec_from_file_location('installer_removals', ROOT / 'build/check-installer-removals.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class InstallerRemovalTests(unittest.TestCase):
    def test_only_explicit_removal_configuration_accepted(self):
        self.assertEqual(check.removal_names(check.PREFIX + '      - casper\n      - calamares\n'),
                         ['casper', 'calamares'])
        for text in ['update_db: true\n', check.PREFIX, check.PREFIX + '      - "^live-*"\n',
                     check.PREFIX + '      - casper\n      - casper\n',
                     check.PREFIX + '      - casper\n  - install:\n      - other\n']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                check.removal_names(text)

    def test_extra_removal_install_or_broken_state_refused(self):
        wanted = ['casper']
        good = [{'name': 'casper', 'operation': 'remove'}]
        check.validate_plan(wanted, good, 0)
        for plan, broken in [(good + [{'name': 'plasma-desktop', 'operation': 'remove'}], 0),
                             ([{'name': 'casper', 'operation': 'unexpected-change'}], 0),
                             ([], 0), (good + good, 0), (good, 1)]:
            with self.subTest(plan=plan, broken=broken), self.assertRaises(ValueError):
                check.validate_plan(wanted, plan, broken)
