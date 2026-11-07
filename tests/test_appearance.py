import importlib.util, json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('appearance_model', ROOT / 'overlay/usr/lib/orez/appearance_model.py')
import sys
m = importlib.util.module_from_spec(spec); sys.modules['appearance_model'] = m; spec.loader.exec_module(m)


class AppearanceModelTests(unittest.TestCase):
    def test_every_offered_choice_has_an_argument_list_plan(self):
        for group in m.GROUPS:
            for opt in m.GROUPS[group][1]:
                for cmd in m.plan(group, opt.id):
                    self.assertIsInstance(cmd, list)
                    self.assertTrue(all(isinstance(a, str) for a in cmd))
                    self.assertNotIn(cmd[0], {'sh', 'bash', 'sudo', 'pkexec'})

    def test_unknown_choices_are_refused(self):
        for group in m.GROUPS:
            with self.assertRaises(ValueError):
                m.plan(group, 'x"; rm -rf ~; "')

    def test_restore_script_only_accepts_validated_panel_values(self):
        good = json.dumps([{'location': 'bottom', 'alignment': 'center', 'lengthMode': 'fill', 'floating': False, 'height': 44}])
        self.assertIn('p.location="bottom"', m.restore_layout_script(good))
        for bad in [{'location': 'bottom");evil();("'}, {'height': 9999}, {'floating': 'yes'}]:
            panel = json.loads(good)[0]; panel.update(bad)
            with self.assertRaises(ValueError):
                m.restore_layout_script(json.dumps([panel]))

    def test_settings_catalogue_offers_appearance(self):
        data = json.loads((ROOT / 'overlay/usr/share/orez/settings-catalog.json').read_text())
        self.assertIn('appearance', [i['action'] for c in data['categories'] for i in c['items']])

    def test_wallpaper_previews_are_real_packaged_images(self):
        for opt in m.GROUPS['wallpaper'][1]:
            images = list((ROOT / 'overlay/usr/share/wallpapers' / opt.id / 'contents/images').glob('*.jpg'))
            self.assertTrue(images)


if __name__ == '__main__':
    unittest.main()
