#!/usr/bin/env python3
"""Disposable VM installation test for an installer-enabled OREZ ISO.

1. Boot the ISO (default entry) with one blank 40 GiB virtual disk; complete
   owner setup and sign in, exactly like ci-vm-login.py.
2. Start "Install OREZ OS" from KRunner, authenticate with the owner password,
   and drive Calamares by OCR: Erase disk (the only, blank, virtual disk),
   create a user, Install, wait for completion.
3. Power off, boot the virtual disk alone with the same UEFI variables, sign in
   at the installed system's login screen, and collect in-guest facts.
Never touches a real disk: the only block device is a qcow2 file made here.
"""
import argparse, csv, importlib.util, io, json, random, re, string, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location('vmlogin', ROOT / 'build/ci-vm-login.py')
vml = importlib.util.module_from_spec(_s); _s.loader.exec_module(vml)
VM = vml.VM


def words(png):
    """OCR word boxes: list of (text, cx, cy)."""
    tsv = subprocess.run(['tesseract', str(png), '-', '--psm', '11', 'tsv'], capture_output=True, text=True).stdout
    out = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter='\t', quoting=csv.QUOTE_NONE):
        t = (row.get('text') or '').strip()
        if t:
            x, y, w, h = (int(row[k]) for k in ('left', 'top', 'width', 'height'))
            out.append((t, x + w // 2, y + h // 2))
    return out


def find(png, phrase, region=None):
    """Centre of the first OCR match of a 1-2 word phrase (letters-only compare),
    optionally restricted to region=(x0, y0, x1, y1)."""
    norm = lambda t: re.sub('[^a-z]', '', t.lower())
    target = phrase.split()
    ws = [w for w in words(png) if not region or (region[0] <= w[1] <= region[2] and region[1] <= w[2] <= region[3])]
    for i, (t, x, y) in enumerate(ws):
        if norm(t) == norm(target[0]):
            if len(target) == 1:
                return x, y
            if i + 1 < len(ws) and norm(ws[i + 1][0]) == norm(target[1]):
                return (x + ws[i + 1][1]) // 2, y
    return None


def click(vm, x, y, w=1280, h=800):
    ev = lambda axis, v: {'type': 'abs', 'data': {'axis': axis, 'value': int(v * 32767 / (w if axis == 'x' else h))}}
    vm.cmd('input-send-event', events=[ev('x', x), ev('y', y)]); time.sleep(0.2)
    vm.cmd('input-send-event', events=[{'type': 'btn', 'data': {'down': True, 'button': 'left'}}]); time.sleep(0.1)
    vm.cmd('input-send-event', events=[{'type': 'btn', 'data': {'down': False, 'button': 'left'}}]); time.sleep(0.5)


BUTTONS = (780, 655, 1200, 720)   # Calamares bottom button row (Back / Next|Install / Cancel)
CONTENT = (330, 60, 1150, 650)    # page content, excluding the sidebar step list


def click_text(vm, phrase, label, timeout=120, region=None):
    end = time.time() + timeout
    while time.time() < end:
        p, _ = vm.shot(label)
        pos = find(p, phrase, region) if p else None
        if pos:
            vm.note(f'click {phrase!r} at {pos}'); click(vm, *pos); return True
        time.sleep(4)
    vm.note(f'{label}: could not find {phrase!r}'); return False


def facts(vm, pw, tag):
    m = lambda n: 'printf "%s\\n" "==O""REZ-' + tag + n + '=="'
    cmd = ("sudo sh -c '{ " + m('BEGIN') + "; cat /etc/orez-release; lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINTS; "
           "findmnt /; cat /proc/cmdline; efibootmgr; loginctl list-sessions --no-legend; " + m('PROCS') +
           "; ps -eo user:20,pid,comm --no-headers; " + m('MORE') +
           "; dpkg -l orez-shell brave-browser vlc gamemode | tail -4; systemctl is-enabled orez-owner-setup.service; "
           "ls /usr/lib/orez; grep PRETTY_NAME /etc/os-release; readlink /etc/alternatives/default.plymouth; "
           "cat /proc/cmdline; journalctl -b -p err --no-pager | tail -60; " + m('END') + "; } > /dev/ttyS0 2>&1'")
    ok = vm.run_on_tty(pw, cmd, '==OREZ-' + tag + 'END==', 120)
    s = vm.serial()
    return s[s.rfind('==OREZ-' + tag + 'BEGIN=='):s.rfind('==OREZ-' + tag + 'END==')] if ok else ''


def login_desktop(vm, pw, label):
    seen = vm.wait_text(['Welcome home', 'Your workspace', 'Orez Owner'], label + '-greeter', 600)
    if not seen: raise RuntimeError(label + ': login screen not seen')
    time.sleep(5)
    if seen in ('Welcome home', 'Your workspace'):
        vm.click(309, 355); vm.keys('ctrl', 'a'); vm.type('orez\n'); time.sleep(2)
        vm.type(pw); time.sleep(1); vm.keys('ret')
    else:
        vm.type(pw + '\n')
    time.sleep(90); vm.shot(label + '-desktop')


def konsole(vm, command, label):
    vm.keys('alt', 'spc'); time.sleep(3); vm.type('Konsole'); time.sleep(3); vm.keys('ret'); time.sleep(8)
    vm.shot(label + '-konsole'); vm.type(command + '\n'); time.sleep(3)


def update_facts(vm, pw, tag):
    m = lambda n: 'printf "%s\\n" "==O""REZ-' + tag + n + '=="'
    wine = ('sudo -u orez env HOME=/home/orez WINEPREFIX=/home/orez/.wine-orez-test WINEDEBUG=-all '
            'WINEDLLOVERRIDES=mscoree,mshtml= timeout 240 wine cmd /c ver')
    cmd = ("sudo sh -c '{ " + m('BEGIN') + "; grep -E \"PRETTY_NAME|^VERSION=\" /etc/os-release; cat /etc/orez-release; uname -r; "
           "dpkg --print-foreign-architectures; dpkg-query -W -f=\"\\${Package} \\${Version} \\${db:Status-Status}\\n\" "
           "orez-shell steam-installer claude-desktop wine wine32:i386 lutris mangohud winetricks \"nvidia-driver-*\" \"linux-modules-nvidia-*\" \"libnvidia-gl-*\" 2>/dev/null | grep installed; "
           "modinfo -F signer nvidia; modinfo -F version nvidia; ls /usr/games; command -v orez-update; " + m('AUD') + "; dpkg --audit; " + m('AUDE') + "; "
           "cat /var/lib/orez/updates.json; " + m('WINE') + "; " + wine + "; echo wine-exit=$?; " + m('LOG') +
           "; tail -40 /var/log/orez-update.log; " + m('END') + "; } > /dev/ttyS0 2>&1'")
    ok = vm.run_on_tty(pw, cmd, '==OREZ-' + tag + 'END==', 420)
    s = vm.serial()
    return s[s.rfind('==OREZ-' + tag + 'BEGIN=='):s.rfind('==OREZ-' + tag + 'END==')] if ok else ''


def update_stage(a, disk, vars_file, pw, r):
    """Installed OREZ 0.1 + OREZ update USB (offline VM) -> OREZ Update window -> restart -> checks."""
    c = r['checks']; out = a.out / 'update'; out.mkdir(exist_ok=True)
    vm = VM(None, out, 6144, 4, disk=disk, vars_file=vars_file, serial_name='serial-update.log', usb=a.update_iso)
    try:
        if vm.wait_text(['GNU GRUB', 'OREZ GNU'], 'u-grub', 120): vm.keys('ret')
        login_desktop(vm, pw, 'u-before')
        # The owner opens the USB once (Dolphin does the same udisks mount), then starts the window.
        konsole(vm, 'udisksctl mount -b /dev/disk/by-label/OREZ_UPDATE && python3 /run/media/orez/OREZ_UPDATE/orez-update/update_ui.py --nvidia', 'u')
        c['update_window'] = bool(vm.wait_text(['is ready to install', 'Install update'], 'u-window', 120))
        if not c['update_window']: raise RuntimeError('OREZ Update window did not show the update')
        time.sleep(2); vm.shot('u-options')  # Steam, Claude (and NVIDIA on NVIDIA PCs) are ticked by default
        c['install_clicked'] = click_text(vm, 'Install update', 'u-install', 20)
        if not c['install_clicked']:
            # Light-on-dark button text defeats OCR; the 760x640 window opens centred, button bottom-right.
            vm.note('u-install: using fixed Install update position'); click(vm, 938, 675)
        c['polkit'] = bool(vm.wait_text(['Authentication Required', 'Authenticate'], 'u-polkit', 90))
        vm.type(pw + '\n')
        res = vm.wait_text(['Update installed', 'was not completed'], 'u-progress', 3600, every=30, keepalive=True)
        vm.shot('u-finished')
        c['update_installed'] = res == 'Update installed'
        if not c['update_installed']: raise RuntimeError('update reported failure')
        c['restart_clicked'] = click_text(vm, 'Restart now', 'u-restart', 20)
        if not c['restart_clicked']:
            vm.note('u-restart: using fixed Restart now position'); click(vm, 938, 675); c['restart_clicked'] = True
        try: vm.proc.wait(240)
        except Exception: vm.note('guest did not power off after restart request')
    except Exception as e:
        r['error_update'] = str(e); vm.note('ERROR ' + str(e))
        try:
            vm.keys('ctrl', 'alt', 'f3'); time.sleep(3); vm.type('orez\n'); time.sleep(2); vm.type(pw + '\n'); time.sleep(4)
            vm.run_on_tty(pw, "sudo sh -c 'tail -150 /var/log/orez-update.log > /dev/ttyS0'", '__x__', 20)
        except Exception: pass
    finally:
        vm.stop(); r['frames_update'] = vm.frames; r['timeline_update'] = vm.log
    if not c.get('update_installed'):
        return
    vm = VM(None, out, 6144, 4, disk=disk, vars_file=vars_file, serial_name='serial-after.log')
    try:
        if vm.wait_text(['GNU GRUB', 'OREZ GNU'], 'a-grub', 120):
            vm.keys('ret')
            for _ in range(15): time.sleep(1); vm.shot('a-splash')
        login_desktop(vm, pw, 'a-after')
        c['after_desktop'] = True
        konsole(vm, 'WINEDEBUG=-all WINEDLLOVERRIDES=mscoree,mshtml= wine notepad', 'a')
        time.sleep(100); vm.shot('a-wine-notepad')
        vm.keys('alt', 'spc'); time.sleep(3); vm.type('Steam'); time.sleep(4); vm.shot('a-krunner-steam'); vm.keys('esc')
        vm.keys('alt', 'spc'); time.sleep(3); vm.type('Lutris'); time.sleep(4); vm.shot('a-krunner-lutris'); vm.keys('esc')
        vm.keys('alt', 'spc'); time.sleep(3); vm.type('Claude'); time.sleep(4); vm.shot('a-krunner-claude'); vm.keys('ret')
        time.sleep(40); vm.shot('a-claude-app'); vm.keys('alt', 'f4'); time.sleep(3)
        vm.keys('ctrl', 'alt', 'f3'); time.sleep(3); vm.type('orez\n'); time.sleep(2); vm.type(pw + '\n'); time.sleep(5)
        blk = update_facts(vm, pw, 'U')
        (out / 'after-update-facts.txt').write_text(blk)
        c['after_os_0_2'] = 'OREZ OS 0.2' in blk
        c['after_i386'] = '\ni386' in blk
        for pk in ('steam-installer', 'wine ', 'lutris', 'orez-shell 0.2', 'claude-desktop'):
            c['after_' + pk.split()[0].replace('-', '_')] = pk in blk
        c['after_nvidia_driver_pkg'] = 'nvidia-driver-' in blk
        c['after_wine_reports_windows'] = 'Microsoft Windows' in blk
        want_k = json.loads((a.update_iso.parent / 'update.json').read_text()).get('kernel_after_update', '') if (a.update_iso.parent / 'update.json').is_file() else ''
        c['after_new_kernel'] = bool(want_k) and want_k in blk
        c['after_nvidia_module_signed'] = 'Canonical' in blk.split('==OREZ-UAUD==')[0]
        c['after_dpkg_clean'] = not blk.split('==OREZ-UAUD==')[-1].split('==OREZ-UAUDE==')[0].strip()
    except Exception as e:
        r['error_after'] = str(e); vm.note('ERROR ' + str(e))
    finally:
        vm.stop(); r['frames_after'] = vm.frames; r['timeline_after'] = vm.log


def main(a):
    a.out.mkdir(parents=True, exist_ok=True)
    disk = a.out / 'disposable-disk.qcow2'
    subprocess.run(['qemu-img', 'create', '-f', 'qcow2', str(disk), '40G'], check=True, stdout=subprocess.DEVNULL)
    vars_file = a.out / 'uefi-vars.fd'
    pw = 'Orez' + ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(18))
    r = {'checks': {}, 'stage': 'live'}; c = r['checks']
    vm = VM(a.iso, a.out, 6144, 4, disk=disk, vars_file=vars_file, serial_name='serial-live.log')
    try:
        c['enroll'] = bool(vm.wait_text(['live-session password'], 'enroll', 900))
        if not c['enroll']: raise RuntimeError('no enrollment prompt')
        time.sleep(2); vm.type(pw + '\n'); time.sleep(2); vm.type(pw + '\n')
        c['greeter'] = bool(vm.wait_text(['Welcome home', 'Your workspace'], 'greeter', 600))
        vm.keys('ctrl', 'a'); vm.type('orez\n'); time.sleep(1); vm.type(pw + '\n')
        time.sleep(90); vm.shot('live-desktop')
        # Start the installer through KRunner (Alt+Space), as a person could.
        vm.keys('alt', 'spc'); time.sleep(3); vm.type('Install OREZ OS'); time.sleep(3); vm.shot('krunner')
        vm.keys('ret'); time.sleep(8)
        c['polkit_prompt'] = bool(vm.wait_text(['Authentication', 'Password'], 'polkit', 60))
        vm.type(pw + '\n')
        c['installer_welcome'] = bool(vm.wait_text(['Welcome to the OREZ', 'OREZ OS 0.1 installer'], 'cal-welcome', 240))
        if not c['installer_welcome']: raise RuntimeError('installer did not open')
        def page(words_, label, timeout=120):
            return bool(vm.wait_text(words_, label, timeout))

        def press(name, label):
            # Calamares' primary button (Next / Install) has a fixed position in this
            # 960x640 window; use it when OCR misses the label. Pages are still
            # confirmed by their own content afterwards.
            if not click_text(vm, name, label, 20, BUTTONS):
                vm.note(f'{label}: using fixed {name} button position'); click(vm, 1007, 688)

        def next_to(words_, label):
            press('Next', 'next-to-' + label); time.sleep(3)
            return page(words_, label)

        c['location_page'] = next_to(['Region', 'Zone', 'timezone'], 'cal-location')
        c['keyboard_page'] = next_to(['Keyboard model', 'test your keyboard'], 'cal-keyboard')
        c['partition_page'] = next_to(['Select storage device', 'Erase disk'], 'cal-partition')
        click_text(vm, 'Erase disk', 'cal-erase', 60, CONTENT); time.sleep(3); vm.shot('cal-erase-selected')
        c['users_page'] = next_to(['What is your name', 'name of this computer'], 'cal-users')
        p, _ = vm.shot('cal-users-fields')
        lab = find(p, 'your name?', CONTENT) or find(p, 'your name', CONTENT)
        if lab: click(vm, lab[0], lab[1] + 30)
        vm.type('Orez Owner'); time.sleep(1)
        vm.keys('tab'); vm.keys('ctrl', 'a'); vm.type('orez')
        vm.keys('tab'); vm.keys('ctrl', 'a'); vm.type('orez-pc')
        vm.keys('tab'); vm.type(pw); vm.keys('tab'); vm.type(pw); time.sleep(2)
        vm.shot('cal-users-filled')
        c['summary_page'] = next_to(['overview', 'install procedure'], 'cal-summary')
        press('Install', 'cal-install'); time.sleep(4)
        c['confirm_dialog'] = click_text(vm, 'Install Now', 'cal-confirm', 30)
        if not c['confirm_dialog']:
            # "Continue with Installation?" dialog: Install Now is at a fixed spot when centred.
            p, txt = vm.shot('cal-confirm-check')
            seen = 'continuewithinstallation' in re.sub('[^a-z]', '', txt.lower()) or 'undo these changes' in txt.lower()
            vm.note(f'cal-confirm: fixed Install Now position (dialog text seen by OCR: {seen})')
            click(vm, 741, 418)  # only a disposable virtual disk exists in this VM
            c['confirm_dialog'] = seen
        r['stage'] = 'installing'
        c['install_finished'] = bool(vm.wait_text(['All done', 'has been installed', 'Installation Failed'], 'cal-progress', 2700, every=20, keepalive=True))
        p, txt = vm.shot('cal-finished')
        c['install_failed_message'] = 'installationfailed' in re.sub('[^a-z]', '', txt.lower())
        (a.out / 'live-calamares-log.txt').write_text('')
        vm.keys('ctrl', 'alt', 'f3'); time.sleep(3); vm.type('orez\n'); time.sleep(2); vm.type(pw + '\n'); time.sleep(4)
        vm.run_on_tty(pw, "sudo sh -c 'tail -300 /root/.cache/calamares/session.log /var/log/installer/debug.log 2>/dev/null > /dev/ttyS0'", '__x__', 20)
    except Exception as e:
        r['error'] = str(e); vm.note('ERROR ' + str(e))
    finally:
        vm.stop()
    if c.get('install_finished') and not c.get('install_failed_message'):
        r['stage'] = 'installed-boot'
        (a.out / 'installed').mkdir(exist_ok=True)
        vm2 = VM(None, a.out / 'installed', 6144, 4, disk=disk, vars_file=vars_file, serial_name='serial-installed.log')
        try:
            # Boot straight from the menu, then capture the boot splash frame by frame.
            if vm2.wait_text(['GNU GRUB', 'OREZ GNU'], 'installed-grub', 120):
                vm2.keys('ret')
                for _ in range(25):
                    time.sleep(1); vm2.shot('installed-splash')
            seen = vm2.wait_text(['Welcome home', 'Your workspace', 'Orez Owner'], 'installed-greeter', 600)
            c['installed_login_screen'] = bool(seen)
            c['installed_orez_greeter'] = seen in ('Welcome home', 'Your workspace')
            if not seen: raise RuntimeError('installed login screen not seen')
            time.sleep(5)
            if c['installed_orez_greeter']:
                # OREZ greeter: username field, then password field (fixed layout at 1280x800).
                vm2.click(309, 355); vm2.keys('ctrl', 'a'); vm2.type('orez\n'); time.sleep(2)
                vm2.type(pw); time.sleep(1); vm2.shot('installed-credentials'); vm2.keys('ret')
            else:
                vm2.type(pw + '\n')
            time.sleep(90); vm2.shot('installed-desktop')
            vml.tour(vm2)
            vm2.keys('ctrl', 'alt', 'f3'); time.sleep(3); vm2.type('orez\n'); time.sleep(2); vm2.type(pw + '\n'); time.sleep(5)
            blk = facts(vm2, pw, 'I')
            (a.out / 'installed-facts.txt').write_text(blk)
            procs = blk.split('==OREZ-IPROCS==')[-1].split('==OREZ-IMORE==')[0]
            owner = [l.split() for l in procs.splitlines() if len(l.split()) == 3 and l.split()[0] == 'orez']
            c['installed_plasmashell'] = any(x[2] == 'plasmashell' for x in owner)
            c['installed_kwin'] = any(x[2].startswith('kwin_wayland') for x in owner)
            c['installed_no_live_owner_setup'] = 'orez_owner' not in blk and 'owner_setup.py' not in blk
        except Exception as e:
            r['error_installed'] = str(e); vm2.note('ERROR ' + str(e))
        finally:
            vm2.stop()
            r['frames_installed'] = vm2.frames
    if a.update_iso and c.get('installed_plasmashell'):
        r['stage'] = 'update'
        update_stage(a, disk, vars_file, pw, r)
        r['update_pass'] = all(c.get(k) for k in ('update_installed', 'after_desktop', 'after_os_0_2', 'after_i386',
                                                   'after_steam_installer', 'after_wine', 'after_lutris',
                                                   'after_orez_shell', 'after_claude_desktop', 'after_wine_reports_windows',
                                                   'after_new_kernel', 'after_nvidia_module_signed'))
    del pw
    r['frames_live'] = vm.frames; r['timeline'] = vm.log
    r['install_pass'] = bool(c.get('install_finished') and not c.get('install_failed_message')
                             and c.get('installed_plasmashell') and c.get('installed_kwin'))
    (a.out / 'install-result.json').write_text(json.dumps(r, indent=2) + '\n')
    print(json.dumps({k: v for k, v in r.items() if not k.startswith('frames')}, indent=2))
    disk.unlink(missing_ok=True)
    if a.update_iso:
        return 0 if r.get('update_pass') else 1
    return 0 if r['install_pass'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--update-iso', type=Path, help='after installing, apply this OREZ update USB image and verify')
    sys.exit(main(p.parse_args()))
