import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from test_live_initrd import builder, entry

ROOT=Path(__file__).resolve().parents[1]


class OwnerInitrdTests(unittest.TestCase):
    def fixture(self):
        old,new=builder.sources();prefix=b'early-owner-test\0'
        plain=entry(builder.HOOK,old)
        for name,previous,replacement in builder.owner_sources(): plain+=entry(name,previous)
        plain+=entry('unrelated-file',b'preserve me')+entry('TRAILER!!!',mode=0)
        data=prefix+builder.pack(plain)
        return prefix,plain,data

    def test_all_reviewed_hooks_roundtrip_and_unrelated_changes_are_rejected(self):
        prefix,plain,data=self.fixture()
        with tempfile.TemporaryDirectory() as directory, patch.multiple(builder,
                EXPECTED_INITRD_SHA256=builder.sha(data),PREFIX_BYTES=len(prefix),
                PREFIX_SHA256=builder.sha(prefix),ARCHIVE_SHA256=builder.sha(plain)):
            root=Path(directory);original=root/'original';result=root/'patched';report=root/'report'
            original.write_bytes(data);builder.patch(original,result,report,True)
            builder.verify(result,report)
            metadata=json.loads(report.read_text())
            self.assertEqual(metadata['schema_version'],3)
            self.assertTrue(metadata['administrator_policy_changed'])
            self.assertFalse(metadata['owner_setup']['effective_policy_tested'])
            self.assertTrue(result.read_bytes().startswith(prefix))
            changed=builder.unpack(result.read_bytes()[len(prefix):]).replace(b'preserve me',b'corrupt! me')
            result.write_bytes(prefix+builder.pack(changed))
            with self.assertRaisesRegex(ValueError,'unrelated changes'):builder.verify(result,report)

    def test_changed_upstream_owner_hook_is_refused(self):
        prefix,plain,data=self.fixture()
        member,old,new=builder.owner_sources()[0]
        with self.assertRaises(ValueError):
            builder.replace_hook(plain,old+b'changed',new,member)

    def test_no_empty_password_grant_autologin_or_emergency_root_shell(self):
        for member,old,new in builder.owner_sources():
            subprocess.run(['sh','-n',str(ROOT/'image/initramfs'/member)],check=True)
            for forbidden in [b'NOPASSWD: ALL',b'passwd -d',b'U6aMy0wojraho',b'Action=*',b'ResultActive=yes',b'User=$USERNAME',b'panic ']:
                self.assertNotIn(forbidden,new)
        login=(ROOT/'image/initramfs/scripts/casper-bottom/15autologin').read_text()
        self.assertIn('owner-required',login);self.assertIn('Relogin=false',login)

    def test_normal_payload_excludes_live_owner_but_live_layer_requires_it(self):
        spec=importlib.util.spec_from_file_location('stage_owner',ROOT/'build/stage-overlay.py')
        stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            stage.stage(ROOT/'overlay',root/'live',live_owner=True)
            self.assertTrue((root/'live/usr/lib/orez/owner_setup.py').is_file())
            self.assertEqual((root/'live/usr/lib/orez/owner_setup.py').stat().st_mode&0o777,0o644)
            stage.stage(ROOT/'overlay',root/'installed',ROOT/'image/installer/installed-files.txt')
            self.assertFalse((root/'installed/usr/lib/orez/owner_setup.py').exists())
            with self.assertRaises(ValueError):
                stage.stage(ROOT/'overlay',root/'bad',ROOT/'image/installer/installed-files.txt',True)

