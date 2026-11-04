import os
import pathlib
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
OVERLAY = ROOT / 'overlay'


class OrezSourceTests(unittest.TestCase):
    def test_wallpaper_svg_parses(self):
        tree = ET.parse(OVERLAY / 'usr/share/backgrounds/orez/orez-ink.svg')
        self.assertEqual(tree.getroot().tag, '{http://www.w3.org/2000/svg}svg')

    def test_desktop_files_have_registered_commands(self):
        for path in OVERLAY.rglob('*.desktop'):
            txt = path.read_text()
            self.assertIn('[Desktop Entry]', txt)
            self.assertIn('Type=Application', txt)
            exec_line = next(line for line in txt.splitlines() if line.startswith('Exec='))[5:]
            if exec_line.startswith('/usr/bin/orez-'):
                self.assertTrue((OVERLAY / exec_line.split()[0].lstrip('/')).exists())

    def test_scripts_syntax(self):
        for script in [*ROOT.joinpath('build').glob('*.sh'), *OVERLAY.joinpath('usr/bin').iterdir()]:
            subprocess.run(['bash', '-n', str(script)], check=True)

    def test_overlay_is_unprivileged_and_visible(self):
        services = sorted(p.name for p in (OVERLAY / 'usr/lib/systemd/system').glob('*.service'))
        self.assertEqual(services, ['orez-gui-verify.service', 'orez-live-verify.service'])
        unit = (OVERLAY / 'usr/lib/systemd/system/orez-live-verify.service').read_text()
        for required in ['ConditionKernelCommandLine=orez.verify=1', 'ConditionKernelCommandLine=boot=casper', 'User=nobody', 'PrivateNetwork=yes', 'ProtectSystem=strict', 'NoNewPrivileges=yes']:
            self.assertIn(required, unit)
        self.assertFalse(list(OVERLAY.rglob('sudoers*')))
        self.assertFalse(list(OVERLAY.rglob('*authorized_keys*')))
        first_login = (OVERLAY / 'etc/xdg/autostart/orez-initialize.desktop').read_text()
        self.assertIn('Exec=/usr/bin/orez-session-init', first_login)

    def test_graphical_witness_is_unprivileged_and_opt_in(self):
        unit = (OVERLAY / 'usr/lib/systemd/system/orez-gui-verify.service').read_text()
        for item in ['User=nobody', 'PrivateNetwork=yes', 'NoNewPrivileges=yes',
                     'ProtectSystem=strict', 'ConditionKernelCommandLine=orez.verify=1']:
            self.assertIn(item, unit)
        script = (OVERLAY / 'usr/bin/orez-gui-verify').read_text()
        self.assertIn('pgrep -x plasmashell', script)
        self.assertIn('OREZ_GUI_DIAG', script)
        self.assertIn('Type=simple', unit)
        self.assertTrue((OVERLAY / 'etc/systemd/system/multi-user.target.wants/orez-gui-verify.service').is_symlink())
        for unsafe in ['sudo ', 'mkfs', 'wipefs', 'curl ', 'passwd', 'mount -o']:
            self.assertNotIn(unsafe, script)

    def test_status_does_not_require_root(self):
        p = subprocess.run([str(OVERLAY / 'usr/bin/orezctl'), 'status'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn('LIVE TEST ONLY', p.stdout)
        self.assertIn('NOT ENABLED', p.stdout)

    def test_orezctl_denies_unknown_commands(self):
        p = subprocess.run([str(OVERLAY / 'usr/bin/orezctl'), 'set-root-password'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_live_boot_witness_is_opt_in_and_read_only(self):
        script = (OVERLAY / 'usr/bin/orez-live-verify').read_text()
        self.assertIn("has_token 'orez.verify=1'", script)
        self.assertIn("has_token 'boot=casper'", script)
        self.assertIn('OREZ_BOOT_PROOF=', script)
        for bad in ['mkfs', 'wipefs', 'curl', 'sudo ', 'passwd', 'systemctl start', 'mount -o']:
            self.assertNotIn(bad, script)

    def test_orez_controls_and_transparency(self):
        ctl = OVERLAY / 'usr/bin/orezctl'
        for command, expected in [('security','security'),('ai','NOT ENABLED'),('appearance','wallpaper')]:
            p = subprocess.run([str(ctl), command], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)
            self.assertIn(expected.lower(),p.stdout.lower())
        self.assertTrue((OVERLAY / 'usr/share/doc/orez/CONTROLS.md').is_file())

    def test_user_can_disable_and_restore_wallpaper_autostart(self):
        ctl = OVERLAY / 'usr/bin/orezctl'
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, XDG_CONFIG_HOME=directory)
            a = subprocess.run([str(ctl),'appearance','disable'],env=env,capture_output=True,text=True)
            self.assertEqual(a.returncode, 0)
            item = pathlib.Path(directory) / 'autostart/orez-initialize.desktop'
            self.assertIn('Hidden=true',item.read_text())
            b = subprocess.run([str(ctl),'appearance','enable'],env=env,capture_output=True,text=True)
            self.assertEqual(b.returncode, 0)
            self.assertFalse(item.exists())

    def test_hardware_preflight_never_uses_disk_write_or_elevation(self):
        script = (OVERLAY / 'usr/bin/orez-preflight').read_text()
        for prohibited in ['sudo ', 'mkfs', 'wipefs', 'parted ', 'fdisk ', 'mount -o', 'dd if=', 'curl ', 'rm -rf', 'nvidia-installer']:
            self.assertNotIn(prohibited, script)
        p = subprocess.run([str(OVERLAY / 'usr/bin/orez-preflight')], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('read-only', p.stdout.lower())
        self.assertIn('not', p.stdout.lower())

    def test_required_project_handoff_documents_exist(self):
        for doc in ['MASTER_BRIEF.md','MASTER_BLUEPRINT.md','AI_HANDOFF.md',
                    'ROADMAP.md','ARCHITECTURE.md','SECURITY.md','HARDWARE.md',
                    'DECISIONS.md','KNOWN_ISSUES.md','BUILD_AND_RELEASE.md',
                    'DESIGN_SYSTEM.md','REQUIREMENTS_TO_TESTS.md']:
            self.assertTrue((ROOT / 'docs' / doc).is_file(), doc)

    def test_installer_source_inspector_never_formats_disks(self):
        src = (ROOT / 'build/check-installer-source.sh').read_text()
        self.assertIn('unsquashfs -cat', src)
        self.assertIn('Certified for SSD installation: NO', src)
        for danger in ['sudo ', 'mkfs.', 'wipefs', 'sgdisk', 'parted ', 'dd if=']:
            self.assertNotIn(danger, src)

    def test_live_installer_is_visibly_disabled_but_host_package_preserves_calamares(self):
        stub = (OVERLAY / 'usr/bin/calamares').read_text()
        self.assertIn('OREZ LIVE TEST', stub)
        self.assertIn('exit 78', stub)
        for forbidden in ['sudo ', 'mkfs', 'wipefs', 'sgdisk', 'parted ', 'dd if=', 'apt install']:
            self.assertNotIn(forbidden, stub)
        desktop = (OVERLAY / 'usr/share/applications/calamares.desktop').read_text()
        self.assertIn('Exec=/usr/bin/calamares', desktop)
        self.assertIn('Unavailable', desktop)
        packaging = (ROOT / 'build/package-shell.sh').read_text()
        self.assertIn('rm -f -- "$work/usr/bin/calamares" "$work/usr/share/applications/calamares.desktop"', packaging)

    def test_install_only_payload_has_strict_file_allowlist(self):
        allowlist = (ROOT / 'image/installer/installed-files.txt').read_text().splitlines()
        names = [row.strip() for row in allowlist if row.strip() and not row.lstrip().startswith('#')]
        self.assertEqual(len(names), len(set(names)))
        self.assertGreaterEqual(len(names), 12)
        for path in names:
            self.assertFalse(path.startswith('/'), path)
            self.assertNotIn('..', path)
            self.assertTrue((OVERLAY / path).is_file(), path)
            self.assertFalse((OVERLAY / path).is_symlink(), path)
        for forbidden in ['usr/bin/calamares', 'etc/sysctl.d/20-apparmor.conf',
                          'usr/bin/orez-live-verify', 'usr/bin/orez-gui-verify']:
            self.assertNotIn(forbidden, names)
        packager = (ROOT / 'build/package-shell.sh').read_text()
        builder = (ROOT / 'build/build-install-payload.sh').read_text()
        self.assertIn('image/installer/installed-files.txt', packager)
        self.assertIn('image/installer/installed-files.txt', builder)
        self.assertIn('mksquashfs', builder)

    def test_candidate_calamares_profile_is_not_active_and_excludes_live_apparmor(self):
        profile = (ROOT / 'image/installer/orez-unpackfs-candidate.conf').read_text()
        self.assertEqual(profile.count('sourcefs: "squashfs"'), 2)
        self.assertIn('source: "/cdrom/casper/filesystem.squashfs"', profile)
        self.assertIn('source: "/cdrom/casper/orez-install.squashfs"', profile)
        self.assertIn('etc/sysctl.d/20-apparmor.conf', profile)
        self.assertFalse((OVERLAY / 'etc/calamares/modules/unpackfs.conf').exists())
        self.assertTrue((OVERLAY / 'usr/bin/calamares').is_file())

    def test_qmp_try_welcome_transition_is_disposable_only(self):
        vm = (ROOT / 'build/test-casper-vm.sh').read_text()
        qmp = (ROOT / 'build/qmp-try-live.sh').read_text()
        self.assertIn('-net none', vm)
        self.assertIn('-device usb-tablet', vm)
        self.assertIn('if [[ "${OREZ_REQUIRE_GUI:-0}" == 1', vm)
        self.assertIn('kubuntu-installer-prompt', vm)
        self.assertIn('qmp-try-live.sh', vm)
        self.assertIn('input-send-event', qmp)
        self.assertIn('x","value":8959', qmp)
        self.assertIn('y","value":26214', qmp)
        for unsafe in ['sudo ', 'mkfs', 'wipefs', 'parted ', 'dd if=', 'curl ', 'apt install']:
            self.assertNotIn(unsafe, qmp)

    def test_qemu_usb_controller_and_safe_welcome_click(self):
        script = (ROOT / 'build/test-casper-vm.sh').read_text()
        self.assertIn('-device qemu-xhci,id=orez-xhci', script)
        self.assertIn('-device usb-tablet,bus=orez-xhci.0', script)
        self.assertIn('check-try-frame.py', script)
        self.assertIn('readonly=on', script)
        self.assertIn('-net none', script)

    def test_welcome_frame_check_accepts_pinned_layout_only(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('orez_frame_check', ROOT / 'build/check-try-frame.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            frame = pathlib.Path(directory) / 'screen.ppm'
            width, height = 1280, 800
            data = bytearray(width * height * 3)
            for x, y, rgb in ((350, 638, (20, 45, 81)), (900, 639, (20, 45, 81)),
                              (640, 740, (0, 24, 61)), (350, 585, (0, 24, 64))):
                idx = (y * width + x) * 3
                data[idx:idx+3] = bytes(rgb)
            frame.write_bytes(b'P6\n1280 800\n255\n' + data)
            self.assertTrue(module.check(frame)[0])
            idx = (638 * width + 350) * 3
            data[idx:idx+3] = b'\x00\x00\x00'
            frame.write_bytes(b'P6\n1280 800\n255\n' + data)
            self.assertFalse(module.check(frame)[0])

    def test_graphical_frame_rejects_blank_even_with_plasma_process(self):
        import importlib.util
        checker = ROOT / 'build/check-graphical-frame.py'
        spec = importlib.util.spec_from_file_location('orez_graphics_frame', checker)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'screen.ppm'
            width, height = 640, 480
            header = b'P6\n640 480\n255\n'
            pixels = bytearray(width * height * 3)
            path.write_bytes(header + pixels)
            self.assertFalse(module.inspect(path)[0])
            for y in range(height):
                for x in range(width):
                    index = (y * width + x) * 3
                    pixels[index:index+3] = bytes(((x + y) % 220 + 30,
                                                    (x * 3) % 255, (y * 2) % 255))
            path.write_bytes(header + pixels)
            self.assertTrue(module.inspect(path)[0])
        source = (ROOT / 'build/test-casper-vm.sh').read_text()
        self.assertIn('check-graphical-frame.py', source)
        self.assertIn('visual_ok=0', source)

    def test_vm_video_adapter_is_test_only_and_allowlisted(self):
        source = (ROOT / 'build/test-casper-vm.sh').read_text()
        self.assertIn('case "$OREZ_VM_VGA" in std|virtio)', source)
        self.assertIn('-vga "$OREZ_VM_VGA"', source)
        self.assertIn('-net none', source)
        self.assertIn('readonly=on', source)
        workflow = (ROOT / '.github/workflows/orez-live.yml').read_text()
        self.assertIn("OREZ_VM_VGA: 'virtio'", workflow)

    def test_blank_try_frame_retries_without_input(self):
        script = (ROOT / 'build/test-casper-vm.sh').read_text()
        self.assertIn('check-graphical-frame.py', script)
        self.assertIn('Try prompt not painted yet; safely retrying', script)
        self.assertIn('NO mouse click sent', script)
        self.assertIn('for ((attempt=0;attempt<305;attempt++))', script)
        workflow = (ROOT / '.github/workflows/orez-live.yml').read_text()
        self.assertIn("OREZ_QEMU_TIMEOUT: '700'", workflow)

    def test_iso_checker_requires_live_installer_safety_guard(self):
        checker = (ROOT / 'build/check-iso.sh').read_text()
        self.assertIn('/casper/zz-orez.squashfs', checker)
        self.assertIn('unsquashfs -cat "$tmp/live.squashfs" usr/bin/calamares', checker)
        self.assertIn("grep -Fq 'OREZ LIVE TEST'", checker)
        self.assertIn("grep -Fqx 'exit 78'", checker)
        self.assertIn('/casper/orez-install.squashfs', checker)

    def test_vm_qpainter_experiment_is_visible_opt_in_only(self):
        relative = 'etc/xdg/plasma-workspace/env/90-orez-vm-software.sh'
        path = OVERLAY / relative
        self.assertTrue(path.is_file())
        contents = path.read_text()
        self.assertIn('orez.verify=1', contents)
        self.assertIn('export KWIN_COMPOSE=Q', contents)
        self.assertIn('case ', contents)
        self.assertNotIn('sudo ', contents)
        self.assertNotIn('curl ', contents)
        self.assertNotIn('mkfs', contents)
        self.assertNotIn(relative, (ROOT / 'image/installer/installed-files.txt').read_text())
        self.assertTrue((OVERLAY / 'usr/share/doc/orez/VM_COMPOSITOR_TEST.md').exists())
        subprocess.run(['sh','-n',str(path)],check=True)
        # In normal test/production sessions without the opt-in kernel flag
        # this script must not overwrite KWIN_COMPOSE.
        command = '. "$1"; printf "%s" "${KWIN_COMPOSE:-unset}"'
        result = subprocess.run(['sh','-c',command,'sh',str(path)],
                                env=dict(os.environ, KWIN_COMPOSE='inherit'),
                                text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout, 'inherit')

    def test_qpainter_kernel_flag_both_branches(self):
        script = OVERLAY / 'etc/xdg/plasma-workspace/env/90-orez-vm-software.sh'
        # Replace only the cat command via a throwaway mock in PATH.
        # No real kernel argument or system setting is modified.
        cases = [
            ('BOOT_IMAGE=test boot=casper orez.verify=1 quiet', 'Q'),
            ('BOOT_IMAGE=test boot=casper quiet', 'inherit'),
            ('BOOT_IMAGE=test orez.verify=10 boot=casper quiet', 'inherit')
        ]
        for cmdline, expected in cases:
            with self.subTest(cmdline=cmdline), tempfile.TemporaryDirectory() as directory:
                mockcat = pathlib.Path(directory) / 'cat'
                mockcat.write_text("#!/bin/sh\nprintf '%s\\n' " + repr(cmdline) + "\n")
                mockcat.chmod(0o755)
                env = dict(os.environ,
                           PATH=directory + os.pathsep + os.environ.get('PATH', ''),
                           KWIN_COMPOSE='inherit')
                result = subprocess.run(
                    ['sh', '-c', '. "$1"; printf "%s" "$KWIN_COMPOSE"', 'sh', str(script)],
                    env=env, capture_output=True, text=True, check=True
                )
                self.assertEqual(result.stdout, expected)

    def test_builder_has_no_raw_disk_writer(self):
        build = (ROOT / 'build/build-live.sh').read_text()
        for dangerous in ['mkfs.', 'wipefs', 'sgdisk', 'parted ', 'dd if=', 'sudo ']:
            self.assertNotIn(dangerous, build)
        self.assertIn('sha256sum -c', build)
        self.assertIn('gpgv', build)
        self.assertIn('-boot_image any replay', build)


if __name__ == '__main__':
    unittest.main(verbosity=2)
