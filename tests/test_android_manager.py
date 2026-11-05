import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('orez_android', ROOT / 'overlay/usr/lib/orez/android_manager.py')
android = importlib.util.module_from_spec(spec)
spec.loader.exec_module(android)


class AndroidManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'managed'
        self.manager = android.Manager(self.root)

    def test_status_does_not_install_or_create_directories(self):
        value = self.manager.status()
        self.assertFalse(value['installed'])
        self.assertFalse(value['autostart'])
        self.assertFalse(self.root.exists())
        self.assertIn('google_apis_playstore', value['system_image'])

    def test_launch_is_accelerated_unrooted_without_host_shares(self):
        command = self.manager.launch_plan()
        self.assertEqual(command[command.index('-accel') + 1], 'on')
        self.assertEqual(command[command.index('-gpu') + 1], 'software')
        self.assertIn(command[command.index('-memory') + 1], ['2048','3072'])
        self.assertNotIn('-writable-system', command)
        self.assertNotIn('-shared-folder', command)
        self.assertNotIn('sudo', command)
        self.assertIn('-no-snapshot', command)

    def test_invalid_configuration_is_rejected(self):
        self.root.mkdir()
        for value in [{'graphics':'software; touch /tmp/bad'}, {'memory_mb':True}, {'memory_mb':99999}, {'cores':0}, {'shell':'bash'}, []]:
            with self.subTest(value=value):
                self.manager.config_file.write_text(json.dumps(value))
                with self.assertRaises(ValueError): self.manager.configuration()

    def test_private_state_permissions(self):
        self.manager.prepare()
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.root / '.orez-managed').stat().st_mode & 0o777, 0o600)

    def test_root_execution_is_rejected(self):
        with patch.object(android.os, 'getuid', return_value=0):
            with self.assertRaisesRegex(ValueError, 'never root'): self.manager.prepare()
        self.assertFalse(self.root.exists())

    def test_unknown_storage_is_not_adopted(self):
        self.root.mkdir(); (self.root / 'keep.txt').write_text('user data')
        with self.assertRaisesRegex(ValueError, 'unrecognized'): self.manager.prepare()
        self.assertEqual((self.root / 'keep.txt').read_text(), 'user data')

    def test_symlink_root_is_rejected(self):
        outside = Path(self.temporary.name) / 'outside'; outside.mkdir()
        self.root.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlink'): self.manager.prepare()

    def test_no_kvm_fails_before_emulator_start(self):
        with patch.object(android.os, 'access', return_value=False), patch.object(android.subprocess, 'Popen') as start:
            with self.assertRaisesRegex(ValueError, 'KVM'): self.manager.start()
            start.assert_not_called()

    def test_reset_requires_exact_confirmation(self):
        with self.assertRaisesRegex(ValueError, 'confirmation'): self.manager.destroy(False, 'yes')
        self.assertFalse(self.root.exists())

    def test_remove_only_managed_runtime_preserves_other_files(self):
        self.manager.prepare(); (self.manager.sdk / 'sample').write_text('SDK')
        sentinel = Path(self.temporary.name) / 'unrelated'; sentinel.write_text('keep')
        self.manager.destroy(True, android.DELETE_CONFIRMATION)
        self.assertFalse((self.manager.sdk / 'sample').exists())
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assertTrue((self.manager.logs / 'actions.jsonl').exists())

    def test_symlink_profile_cannot_erase_external_directory(self):
        self.manager.prepare()
        external = Path(self.temporary.name) / 'external'; external.mkdir(); (external / 'keep').write_text('keep')
        self.manager.profile.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'aliased'): self.manager.destroy(False, android.DELETE_CONFIRMATION)
        self.assertTrue((external / 'keep').exists())

    def test_unrelated_pid_cannot_be_stopped(self):
        self.manager.prepare()
        self.manager.write_json(self.manager.state_file, {'pid':os.getpid(), 'start_ticks':'wrong'})
        with patch.object(android.os, 'killpg') as kill:
            self.manager.stop(); kill.assert_not_called()

    def test_bootstrap_cancellation_downloads_nothing(self):
        with patch.object(android.shutil, 'which', return_value='/usr/bin/java'), patch.object(android.shutil, 'disk_usage') as disk, patch('builtins.input', return_value='NO'), patch.object(android.urllib.request, 'urlopen') as network:
            disk.return_value.free = 30 * 2**30
            with self.assertRaisesRegex(ValueError, 'cancelled'): self.manager.bootstrap()
            network.assert_not_called()

    def test_archive_traversal_and_symlink_rejected(self):
        archive = Path(self.temporary.name) / 'bad.zip'
        for name in ['../outside', '/cmdline-tools/absolute', 'cmdline-tools/../../escape', 'cmdline-tools\\escape']:
            with zipfile.ZipFile(archive, 'w') as z: z.writestr(name, 'bad')
            with self.assertRaisesRegex(ValueError, 'Unsafe'): android.Manager.extract_tools(archive, Path(self.temporary.name) / 'stage')
        with zipfile.ZipFile(archive, 'w') as z:
            info = zipfile.ZipInfo('cmdline-tools/bin/sdkmanager'); info.external_attr = 0o120777 << 16; z.writestr(info, '/etc/passwd')
        with self.assertRaisesRegex(ValueError, 'Unsafe'): android.Manager.extract_tools(archive, Path(self.temporary.name) / 'stage')

    def test_valid_archive_has_accessible_nonprivileged_modes(self):
        archive = Path(self.temporary.name) / 'good.zip'; target = Path(self.temporary.name) / 'stage'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('cmdline-tools/bin/sdkmanager', '#!/bin/sh\nexit 0\n')
            z.writestr('cmdline-tools/lib/data.txt', 'data')
        android.Manager.extract_tools(archive, target)
        self.assertEqual((target / 'cmdline-tools/bin/sdkmanager').stat().st_mode & 0o7777, 0o755)
        self.assertEqual((target / 'cmdline-tools/lib/data.txt').stat().st_mode & 0o7777, 0o644)

    def test_adb_is_private_loopback_and_separate_from_normal_development(self):
        environment = self.manager.environment()
        self.assertEqual(environment['ADB_SERVER_SOCKET'], 'tcp:localhost:5038')
        self.assertEqual(environment['ANDROID_AVD_HOME'], str(self.manager.avds))

    def test_six_gib_host_gets_smaller_guest_default(self):
        with patch.object(android, 'memory_budget', return_value={'total_mb':6144,'available_mb':5000}):
            self.assertEqual(self.manager.configuration()['memory_mb'],2048)

    def test_sixteen_gib_host_gets_bounded_guest_default(self):
        with patch.object(android, 'memory_budget', return_value={'total_mb':16384,'available_mb':12000}):
            self.assertEqual(self.manager.configuration()['memory_mb'],3072)

    def test_memory_pressure_prevents_guest_start(self):
        self.manager.prepare(); self.manager.profile.mkdir()
        with patch.object(android.os, 'access', return_value=True), patch.object(android, 'memory_budget', return_value={'total_mb':6144,'available_mb':2500}), patch.object(android.subprocess, 'Popen') as start:
            with self.assertRaisesRegex(ValueError, 'available memory'): self.manager.start()
            start.assert_not_called()


class WallpaperTests(unittest.TestCase):
    def test_owner_images_are_unchanged(self):
        import hashlib
        manifest = json.loads((ROOT / 'docs/WALLPAPER_SOURCES.json').read_text())
        for item in manifest['assets']:
            path = ROOT / 'overlay/usr/share/wallpapers' / ('OREZ-' + item['name']) / 'contents/images/1280x720.jpg'
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item['sha256'])
            self.assertTrue(path.read_bytes().startswith(b'\xff\xd8'))

    def test_first_login_uses_owner_default(self):
        source = (ROOT / 'overlay/usr/bin/orez-session-init').read_text()
        self.assertIn('/usr/share/wallpapers/OREZ-Rest/contents/images/1280x720.jpg', source)
        self.assertIn('[[ -f "$marker" ]] && exit 0', source)

    def test_preview_uses_same_unmodified_wallpaper(self):
        native = ROOT / 'overlay/usr/share/wallpapers/OREZ-Rest/contents/images/1280x720.jpg'
        self.assertEqual(native.read_bytes(), (ROOT / 'preview/public/orez-rest.jpg').read_bytes())
