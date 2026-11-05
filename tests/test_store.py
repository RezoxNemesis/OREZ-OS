import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('store_manager',ROOT/'overlay/usr/lib/orez/store_manager.py')
store=importlib.util.module_from_spec(spec);spec.loader.exec_module(store)
CATALOG=ROOT/'overlay/usr/share/orez/store-catalog.json'

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.manager=store.Store(self.root/'store',CATALOG)
    def tearDown(self):self.temp.cleanup()
    def test_requested_apps_are_android_and_never_web_fallbacks(self):
        for key in ['youtube','instagram','free-fire','subway-surfers','asphalt-legends','play-store']:
            self.assertEqual(self.manager.app(key)['kind'],'android')
            state=self.manager.status(key)
            self.assertFalse(state['web_fallback']);self.assertFalse(state['installed'])
            self.assertFalse(state['consumer_provider_qualified'])
            with self.assertRaisesRegex(ValueError,'not be replaced with a website'):self.manager.launch_plan(key)
        self.assertNotIn('web',{app['kind'] for app in self.manager.apps.values()})
    def test_official_linux_versions_are_preferred_without_android_duplicates(self):
        for key in ['brave-linux','chrome-linux']:
            self.assertEqual(self.manager.app(key)['kind'],'native')
            self.assertIn('(Linux)',self.manager.app(key)['name'])
        self.assertNotIn('brave',self.manager.apps)
        self.assertNotIn('chrome',self.manager.apps)
    def test_status_does_not_create_directories_or_start_processes(self):
        with patch.object(store.subprocess,'Popen') as spawn:
            self.manager.status('youtube');spawn.assert_not_called()
        self.assertFalse(self.manager.root.exists())
    def test_root_is_rejected_before_actions(self):
        with patch.object(store.os,'geteuid',return_value=0),patch.object(store.subprocess,'Popen') as spawn:
            with self.assertRaises(ValueError):self.manager.runtime_controls(True)
            spawn.assert_not_called()
    def test_runtime_controls_require_explicit_acknowledgement(self):
        with patch.object(store.subprocess,'Popen') as spawn:
            with self.assertRaises(ValueError):self.manager.runtime_controls()
            spawn.assert_not_called()
            self.manager.runtime_controls(True)
            self.assertEqual(spawn.call_args.args[0],['/usr/bin/orez-android','gui'])
            self.assertNotIn('shell',spawn.call_args.kwargs)
    def test_publisher_info_requires_consent_and_never_installs_app(self):
        with patch.object(store.subprocess,'Popen') as spawn:
            with self.assertRaises(ValueError):self.manager.open_source('youtube')
            spawn.assert_not_called()
            self.manager.open_source('youtube',True)
            self.assertEqual(spawn.call_args.args[0],['/usr/bin/xdg-open','https://play.google.com/store/apps/details?id=com.google.android.youtube'])
    def test_native_launch_uses_fixed_binary_no_catalog_execution(self):
        with patch.object(self.manager,'executable',return_value='/usr/bin/vlc'),patch.object(store.subprocess,'Popen') as spawn:
            self.manager.launch('vlc')
            self.assertEqual(spawn.call_args.args[0],['/usr/bin/vlc'])
            self.assertNotIn('shell',spawn.call_args.kwargs)
        self.assertEqual(self.manager.root.stat().st_mode&0o777,0o700)
        self.assertEqual((self.manager.root/'actions.jsonl').stat().st_mode&0o777,0o600)
        record=json.loads((self.manager.root/'actions.jsonl').read_text().splitlines()[-1])
        self.assertEqual(set(record),{'utc','action','app'})
    def test_unknown_app_and_command_injection_rejected(self):
        for key in ['../youtube','youtube;id','--help','https://example.com']:
            with self.assertRaises(ValueError):self.manager.launch_plan(key)
    def test_symlink_or_unrecognized_store_data_not_adopted(self):
        outside=self.root/'outside';outside.mkdir();self.manager.root.symlink_to(outside)
        with self.assertRaises(ValueError):self.manager.prepare()
        self.assertFalse(list(outside.iterdir()))
        self.manager.root.unlink();self.manager.root.mkdir();(self.manager.root/'keep').write_text('keep')
        with self.assertRaises(ValueError):self.manager.prepare()
        self.assertEqual((self.manager.root/'keep').read_text(),'keep')
    def test_invalid_catalog_schema_and_web_kind_are_rejected(self):
        original=json.loads(CATALOG.read_text())
        cases=[[],None,{'schema_version':1,'apps':[42]}]
        for field,value in [('kind','web'),('url','file:///etc/passwd'),('exec','sudo bad'),('name','Bad\nExec=bad')]:
            data=json.loads(json.dumps(original));data['apps'][0][field]=value;cases.append(data)
        for data in cases:
            path=self.root/'catalog';path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):store.read_catalog(path)
    def test_no_web_app_launch_flags_or_privileged_helper(self):
        source=(ROOT/'overlay/usr/lib/orez/store_manager.py').read_text()
        for bad in ['shell=True','--no-sandbox','--app=','--user-data-dir=','pkexec','sudo ','apt-get install']:
            self.assertNotIn(bad,source)
        self.assertFalse((ROOT/'overlay/etc/xdg/autostart/orez-store.desktop').exists())
