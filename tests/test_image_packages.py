import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('image_packages',ROOT/'build/image_packages.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ImagePackageTests(unittest.TestCase):
    def change(self):
        return {'name':'vlc','architecture':'amd64','version':'1.0','previous_version':None,
                'operation':'install','uri':'https://archive.ubuntu.com/ubuntu/pool/vlc.deb',
                'sha256':hashlib.sha256(b'payload').hexdigest(),'bytes':7,'trusted':True,'file':'vlc.deb'}
    def test_valid_profile(self):self.assertEqual(module.profile(ROOT/'image/desktop-packages.json')['release'],'resolute')
    def test_profile_rejects_shell_syntax_duplicates_and_boot_updates(self):
        value=module.profile(ROOT/'image/desktop-packages.json')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'profile.json'
            for names in [['vlc; id'],['vlc','vlc'],['sudo'],['linux-image-generic']]:
                value['packages']=names;path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):module.profile(path)
    def test_inventory_preserves_multiarch_and_ignores_removed_packages(self):
        text='Package: libtest\nArchitecture: amd64\nVersion: 1\nStatus: install ok installed\n\nPackage: libtest\nArchitecture: i386\nVersion: 1\nStatus: install ok installed\n\nPackage: removed\nStatus: deinstall ok config-files'
        self.assertEqual(module.installed(text),{'libtest:amd64':'1','libtest:i386':'1'})
        with self.assertRaises(ValueError):module.installed(text+'\n\n'+text)
    def test_key_pins_ignore_subkey_and_require_primary(self):
        self.assertEqual(module.key_fingerprints('pub:::::::::\nfpr:::::::::ABCDEFABCDEFABCDEFABCDEFABCDEFABCDEFABCD:\nsub:::::::::\nfpr:::::::::1111111111111111111111111111111111111111:'),{'ABCDEFABCDEFABCDEFABCDEFABCDEFABCDEFABCD'})
    def test_untrusted_and_weak_hash_rejected(self):
        for field,value in [('trusted',False),('trusted','false'),('trusted',1),('sha256','0'*32),('bytes',0),('architecture','arm64')]:
            change=self.change();change[field]=value
            with self.assertRaises(ValueError):module.validate_change(change)
    def test_removal_downgrade_and_protected_upgrade_rejected(self):
        for op in ['remove','downgrade']:
            change=self.change();change['operation']=op
            with self.assertRaises(ValueError):module.validate_change(change)
        for name in ['sudo','polkitd','libpam0g','linux-image-generic','systemd','openssh-server','grub-efi-amd64']:
            change=self.change();change['name']=name
            with self.assertRaises(ValueError):module.validate_change(change)
    def test_uri_rejects_alternate_host_insecure_transport_and_credentials(self):
        for uri in ['http://archive.ubuntu.com/vlc.deb','https://evil.invalid/vlc.deb','https://user:secret@archive.ubuntu.com/vlc.deb','https://archive.ubuntu.com:8443/vlc.deb','https://archive.ubuntu.com/vlc.deb?token=x']:
            change=self.change();change['uri']=uri
            with self.assertRaises(ValueError):module.validate_change(change)
    def test_brave_repository_cannot_supply_ubuntu_packages(self):
        change=self.change();change['uri']='https://'+module.BRAVE_SITE+'/pool/app.deb'
        with self.assertRaises(ValueError):module.validate_change(change)
        change['name']='brave-browser';module.validate_change(change)
    def test_filename_cannot_escape_bundle(self):
        for name in ['../app.deb','/app.deb','a\\b.deb','app.txt']:
            change=self.change();change['file']=name
            with self.assertRaises(ValueError):module.validate_change(change)
    def test_integrity_rejects_modified_missing_extra_and_symlink_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'debs').mkdir();payload=root/'debs/vlc.deb';payload.write_bytes(b'payload')
            manifest={'schema':1,'purpose':'orez-image-app-packages','installation_approved':False,'changes':[self.change()]}
            (root/'manifest.json').write_text(json.dumps(manifest));module.verify_bundle(root)
            payload.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):module.verify_bundle(root)
            payload.write_bytes(b'payload');(root/'debs/extra.deb').write_bytes(b'x')
            with self.assertRaises(ValueError):module.verify_bundle(root)
            (root/'debs/extra.deb').unlink();payload.unlink()
            with self.assertRaises(ValueError):module.verify_bundle(root)
            outside=root/'outside';outside.write_bytes(b'payload');payload.symlink_to(outside)
            with self.assertRaises(ValueError):module.verify_bundle(root)
    def test_exact_transaction_preserves_unrelated_base(self):
        before={'systemd:amd64':'1','libtest:i386':'2'};after={**before,'vlc:amd64':'1.0'}
        module.verify_transition(before,after,[self.change()])
        for invalid in [{**after,'systemd:amd64':'2'},{**after,'unexpected:amd64':'3'},{'vlc:amd64':'1.0'}]:
            with self.assertRaises(ValueError):module.verify_transition(before,invalid,[self.change()])
    def test_stale_plan_rejected(self):
        change=self.change();change.update(operation='upgrade',previous_version='old')
        with self.assertRaises(ValueError):module.verify_transition({'vlc:amd64':'other'},{'vlc:amd64':'1.0'},[change])
