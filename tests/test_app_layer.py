import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'build'))
import app_layer
spec=importlib.util.spec_from_file_location('stage_root',ROOT/'build/stage-image-root.py')
staging=importlib.util.module_from_spec(spec);spec.loader.exec_module(staging)
spec=importlib.util.spec_from_file_location('pack_layer',ROOT/'build/pack-app-layer.py')
packing=importlib.util.module_from_spec(spec);spec.loader.exec_module(packing)


class AppLayerTests(unittest.TestCase):
    def item(self,kind='file',mode=0o644):return {'type':kind,'mode':mode,'uid':0,'gid':0,'xattrs':{}}
    def test_deleted_file_is_not_silently_left_in_lower_layer(self):
        with self.assertRaisesRegex(ValueError,'deletions'):app_layer.delta({'usr/share/old':self.item()},{})
    def test_policy_and_autostart_changes_are_rejected(self):
        for path in ['etc/shadow','etc/sudoers.d/backdoor','etc/polkit-1/rules.d/admin.rules','usr/lib/systemd/system/agent.service','boot/vmlinuz','etc/ld.so.preload','etc/cron.daily/agent','root/.ssh/authorized_keys']:
            with self.assertRaises(ValueError):app_layer.delta({},{path:self.item()})
    def test_unreviewed_privileged_binary_rejected(self):
        with self.assertRaises(ValueError):app_layer.delta({},{'usr/bin/app':self.item(mode=0o4755)})
        app_layer.delta({},{'opt/brave.com/brave/chrome-sandbox':self.item(mode=0o4755)})
        for item in [self.item(mode=0o6755),self.item('link',0o4755),{**self.item(mode=0o4755),'uid':1500}]:
            with self.assertRaises(ValueError):app_layer.delta({},{'opt/brave.com/brave/chrome-sandbox':item})
    def test_file_capabilities_cannot_bypass_setuid_review(self):
        item={**self.item(),'xattrs':{'security.capability':'AA=='}}
        with self.assertRaisesRegex(ValueError,'capabilities'):app_layer.delta({},{'usr/bin/new-app':item})
    def test_inode_type_change_is_not_approximated(self):
        with self.assertRaises(ValueError):app_layer.delta({'usr/lib/example':self.item('directory')},{'usr/lib/example':self.item('link')})
    def test_path_traversal_rejected(self):
        for path in ['/etc/new','../etc/new','usr/../etc/new']:
            with self.assertRaises(ValueError):app_layer.delta({},{path:self.item()})
    def test_file_content_metadata_and_link_changes_are_recorded(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'root';root.mkdir();(root/'usr').mkdir();(root/'usr/unchanged').write_text('keep')
            before=app_layer.inventory(root)
            (root/'usr/app').write_text('new');(root/'usr/app').chmod(0o755);(root/'usr/link').symlink_to('/usr/app')
            after=app_layer.inventory(root);changed=app_layer.delta(before,after)
            self.assertEqual(set(changed),{'usr/app','usr/link'})
            self.assertEqual(changed['usr/link']['target'],'/usr/app')
            self.assertEqual(changed['usr/app']['mode'],0o755)
    def test_inventory_never_follows_absolute_directory_alias(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'alias').symlink_to('/etc')
            self.assertEqual(set(app_layer.inventory(root)),{'alias'})
    def test_runtime_and_build_logs_are_not_redistributed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ['run/secret','dev/null','var/log/build','var/cache/apt/cache']:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('not shipped')
            result=app_layer.inventory(root)
            self.assertFalse(any(x in result for x in ['run/secret','dev/null','var/log/build','var/cache/apt/cache']))
    def test_work_guard_rejects_host_roots_and_aliases(self):
        for path in ['/','/etc','/work/../etc','/work/nested/root']:
            with self.assertRaises(ValueError):staging.work_path(path)
    def test_xattrs_on_original_ancestor_are_not_overlooked(self):
        before={'usr':self.item('directory')};after={**before,'usr/app':self.item()}
        self.assertEqual(set(packing.expected_layer(before,after)),{'usr','usr/app'})
        records=packing.pseudo_xattrs(['usr D 0 755 0 0\n','usr x user.policy=value\n','usr/bin/ping x security.capability=0t\\001\n'])
        self.assertEqual(set(records)&set(packing.expected_layer(before,after)),{'usr'})
    def test_ambiguous_original_xattr_paths_fail_closed(self):
        for line in ['../bad x user.policy=value','/usr x user.policy=value','usr\\040space x user.policy=value','usr x malformed']:
            with self.assertRaises(ValueError):packing.pseudo_xattrs([line])
