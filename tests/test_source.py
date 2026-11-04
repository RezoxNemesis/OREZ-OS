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

    def test_builder_has_no_raw_disk_writer(self):
        build = (ROOT / 'build/build-live.sh').read_text()
        for dangerous in ['mkfs.', 'wipefs', 'sgdisk', 'parted ', 'dd if=', 'sudo ']:
            self.assertNotIn(dangerous, build)
        self.assertIn('sha256sum -c', build)
        self.assertIn('gpgv', build)
        self.assertIn('-boot_image any replay', build)


if __name__ == '__main__':
    unittest.main(verbosity=2)
