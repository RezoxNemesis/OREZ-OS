#!/usr/bin/env python3
"""Disposable UEFI VM test of the OREZ live login, driven through QEMU's QMP.

Diskless, offline guest; a random throwaway password created per run and never
written to evidence. Default GRUB entry, no edited kernel flags. Every frame is
kept (PNG). The verdict comes from in-guest facts written to the serial port
(loginctl / process list / journal), not from "screen looks non-blank".
"""
import argparse, json, os, random, re, socket, string, subprocess, sys, tempfile, time
from pathlib import Path

KEY = {c: c for c in string.ascii_lowercase + string.digits}
KEY.update({' ': 'spc', '-': 'minus', '=': 'equal', '.': 'dot', ',': 'comma', '/': 'slash', ';': 'semicolon',
            "'": 'apostrophe', '\n': 'ret', '\t': 'tab', '[': 'bracket_left', ']': 'bracket_right', '\\': 'backslash'})
SHIFT = {'_': 'minus', '+': 'equal', '>': 'dot', '<': 'comma', '?': 'slash', ':': 'semicolon', '"': 'apostrophe',
         '|': 'backslash', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8',
         '(': '9', ')': '0', '{': 'bracket_left', '}': 'bracket_right', '~': 'grave_accent'}


class VM:
    def __init__(self, iso, out, ram, cpus, disk=None, vars_file=None, serial_name='serial.log'):
        self.out = out; self.frames = []; self.t0 = time.time(); self.log = []
        self.tmp = Path(tempfile.mkdtemp(prefix='orez-vm-'))
        code = next(p for p in ['/usr/share/OVMF/OVMF_CODE_4M.fd', '/usr/share/OVMF/OVMF_CODE.fd'] if os.path.exists(p))
        vars_ = code.replace('CODE', 'VARS')
        self.vars = Path(vars_file) if vars_file else self.tmp / 'vars.fd'
        if not self.vars.exists():
            subprocess.run(['cp', vars_, self.vars], check=True)
        self.serial_path = out / serial_name
        accel = 'kvm' if os.access('/dev/kvm', os.W_OK) else 'tcg'
        self.note('accelerator=' + accel)
        self.proc = subprocess.Popen([
            'qemu-system-x86_64', '-machine', 'q35,accel=' + accel, '-cpu', 'host' if accel == 'kvm' else 'max',
            '-m', str(ram), '-smp', str(cpus),
            '-drive', f'if=pflash,format=raw,unit=0,readonly=on,file={code}',
            '-drive', f'if=pflash,format=raw,unit=1,file={self.vars}',
            '-device', 'ahci,id=ahci',
            *(['-drive', f'if=none,id=cd,media=cdrom,format=raw,readonly=on,file={iso}',
               '-device', 'ide-cd,drive=cd,bus=ahci.0,bootindex=1'] if iso else []),
            *(['-drive', f'if=none,id=hd,format=qcow2,file={disk}',
               '-device', 'virtio-blk-pci,drive=hd,bootindex=2'] if disk else []),
            '-device', 'virtio-vga', '-display', 'none', '-usb', '-device', 'usb-tablet',
            '-qmp', f'unix:{self.tmp}/qmp.sock,server=on,wait=off',
            '-serial', f'file:{self.serial_path}', '-nic', 'none', '-no-reboot'])
        for _ in range(60):
            if (self.tmp / 'qmp.sock').exists(): break
            time.sleep(0.5)
        self.s = socket.socket(socket.AF_UNIX); self.s.connect(str(self.tmp / 'qmp.sock'))
        self.f = self.s.makefile('rw'); self.f.readline(); self.cmd('qmp_capabilities')

    def note(self, m):
        line = f'{time.time() - self.t0:7.1f}s {m}'; print(line, flush=True); self.log.append(line)

    def cmd(self, name, **args):
        self.f.write(json.dumps({'execute': name, 'arguments': args} if args else {'execute': name}) + '\n'); self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if 'return' in r or 'error' in r: return r

    def keys(self, *codes):
        self.cmd('send-key', keys=[{'type': 'qcode', 'data': c} for c in codes]); time.sleep(0.08)

    def type(self, text):
        for ch in text:
            if ch in KEY: self.keys(KEY[ch])
            elif ch.lower() in KEY and ch.isupper(): self.keys('shift', KEY[ch.lower()])
            elif ch in SHIFT: self.keys('shift', SHIFT[ch])
            else: raise ValueError('untypeable character')

    def shot(self, label):
        p = self.out / f'{len(self.frames):03d}-{label}.png'
        r = self.cmd('screendump', filename=str(p), format='png')
        if 'error' in r: self.note('screendump error ' + str(r)); return None, ''
        self.frames.append(p.name)
        return p, self.ocr(p)

    @staticmethod
    def ocr(p, psm='3'):
        return subprocess.run(['tesseract', str(p), '-', '--psm', psm], capture_output=True, text=True).stdout

    def wait_text(self, words, label, timeout, every=5):
        """OCR is noisy: compare letters only and retry a second page mode."""
        norm = lambda t: re.sub('[^a-z]', '', t.lower())
        wanted = [(w, norm(w)) for w in words]
        end = time.time() + timeout
        while time.time() < end:
            if self.proc.poll() is not None: raise RuntimeError('guest stopped')
            p, txt = self.shot(label)
            for attempt in (txt, self.ocr(p, '6') if p else ''):
                low = norm(attempt)
                hit = [w for w, n in wanted if n in low]
                if hit: self.note(f'{label}: saw {hit[0]!r}'); return hit[0]
            time.sleep(every)
        self.note(f'{label}: timeout waiting for {words}'); return None

    def serial(self):
        return self.serial_path.read_text(errors='replace')

    def run_on_tty(self, password, command, marker, timeout=60):
        self.type(command + '\n'); time.sleep(3)
        _, txt = self.shot('sudo')
        if 'password' in txt.lower(): self.type(password + '\n')
        end = time.time() + timeout
        while time.time() < end:
            if marker in self.serial(): return True
            time.sleep(2)
        return False

    def stop(self):
        try: self.cmd('quit')
        except Exception: pass
        try: self.proc.wait(20)
        except Exception: self.proc.kill()


def main(a):
    a.out.mkdir(parents=True, exist_ok=True)
    pw = 'Orez' + ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(18))
    vm = VM(a.iso, a.out, a.ram, a.cpus); result = {'iso': str(a.iso), 'checks': {}}
    try:
        # Type only once the hidden-input prompt itself is visible (never earlier).
        seen = vm.wait_text(['live-session password'], 'enroll', 900)
        result['checks']['enrollment_prompt'] = bool(seen)
        if not seen: raise RuntimeError('no enrollment prompt')
        time.sleep(2)
        vm.type(pw + '\n'); time.sleep(2); vm.shot('after-first-entry')
        vm.type(pw + '\n'); time.sleep(2)
        result['checks']['greeter'] = bool(vm.wait_text(['Welcome home', 'Your workspace', 'Sign in uses your local'], 'greeter', 600))
        if not result['checks']['greeter']: raise RuntimeError('no greeter')
        vm.keys('ctrl', 'a'); vm.type('orez\n'); time.sleep(1); vm.type(pw); vm.shot('credentials-entered')
        vm.keys('ret'); vm.note('submitted graphical login')
        returned = False
        for i in range(a.desktop_wait // 10):
            time.sleep(10); _, txt = vm.shot('after-login')
            if 'welcome home' in txt.lower() and i >= 2: returned = True; vm.note('greeter returned'); break
        result['checks']['greeter_returned_after_login'] = returned
        # Collect objective in-guest facts from an authenticated owner console.
        vm.keys('ctrl', 'alt', 'f3'); time.sleep(4); vm.shot('tty3')
        vm.type('orez\n'); time.sleep(2); vm.type(pw + '\n'); time.sleep(5); vm.shot('tty3-login')
        def mark(name):
            # Assembled at run time ("==O""REZ") so the typed command, or a journal line
            # quoting it, can never be mistaken for real output.
            return 'printf "%s\\n" "==O""REZ-' + name + '=="'

        def collect(tag, full=True):
            parts = ["loginctl list-sessions --no-legend", mark(tag + 'PROCS'), "ps -eo user:20,pid,comm --no-headers",
                     mark(tag + 'LOOK'), "for p in $(pgrep -u orez -x plasmashell); do tr \\\\0 \\\\n < /proc/$p/environ | grep ^XDG_CONFIG_DIRS; done",
                     "grep -h -E \"^(Image|LookAndFeelPackage|ColorScheme)=\" /home/orez/.config/plasma-org.kde.plasma.desktop-appletsrc /home/orez/.config/kdeglobals",
                     "ls /home/orez/Desktop"]
            if full:
                parts += [mark(tag + 'TRACE'), "journalctl -b --no-pager -o short-precise -t orez-session-trace",
                          mark(tag + 'SDDM'), "journalctl -b --no-pager -o short-precise -u sddm | tail -80",
                          mark(tag + 'SESSIONLOG'), "tail -200 /home/orez/.local/share/sddm/wayland-session.log",
                          mark(tag + 'USERJOURNAL'), "journalctl -b --no-pager -o short-precise _UID=1000 | tail -300",
                          mark(tag + 'COREDUMPS'), "coredumpctl list --no-pager | tail -20"]
            cmd = "sudo sh -c '{ " + mark(tag + 'BEGIN') + "; " + "; ".join(parts) + "; " + mark(tag + 'END') + "; } > /dev/ttyS0 2>&1'"
            ok = vm.run_on_tty(pw, cmd, '==OREZ-' + tag + 'END==', 120)
            ser = vm.serial()
            blk = ser[ser.rfind('==OREZ-' + tag + 'BEGIN=='):ser.rfind('==OREZ-' + tag + 'END==')] if ok else ''
            sec = blk.split('==OREZ-' + tag + 'PROCS==')[-1].split('==OREZ-' + tag + 'LOOK==')[0] if blk else ''
            owner = [l.split() for l in sec.splitlines() if len(l.split()) == 3 and l.split()[0] == 'orez']
            look = blk.split('==OREZ-' + tag + 'LOOK==')[-1].split('==OREZ-' + tag + 'TRACE==')[0] if blk else ''
            return ok, blk, owner, look

        got, block, owner, look = collect('')
        c = result['checks']
        c['facts_collected'] = got
        c['plasmashell_running'] = any(p[2] == 'plasmashell' for p in owner)
        c['kwin_running_for_owner'] = any(p[2].startswith('kwin_wayland') for p in owner)
        c['owner_graphical_session'] = any('orez' in l and 'seat0' in l and 'tty2' in l for l in block.split('==OREZ-PROCS==')[0].splitlines())
        c['orez_defaults_in_session'] = '/etc/xdg/orez' in look
        c['orez_wallpaper'] = 'OREZ-Rest' in look
        (a.out / 'guest-facts.txt').write_text(block)
        # Sign out the way a person does (Plasma's own logout), then sign in again.
        # Pass only if a NEW plasmashell process exists afterwards.
        first_pids = {p[1] for p in owner if p[2] == 'plasmashell'}
        vm.run_on_tty(pw, "sudo -u orez env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus "
                          "qdbus6 org.kde.Shutdown /Shutdown org.kde.Shutdown.logout", '__never__', 10)
        vm.keys('ctrl', 'alt', 'f1'); time.sleep(3)
        c['greeter_after_signout'] = bool(vm.wait_text(['Welcome home', 'Your workspace'], 'greeter-2', 180))
        if c['greeter_after_signout']:
            time.sleep(5)  # let the greeter settle before typing
            vm.keys('ctrl', 'a'); vm.type('orez'); vm.keys('tab'); time.sleep(1); vm.type(pw); time.sleep(1)
            vm.shot('credentials-2'); vm.keys('ret'); vm.note('second graphical login')
            returned2 = False
            for i in range(9):
                time.sleep(10); _, txt = vm.shot('after-login-2')
                if 'signinfailed' in re.sub('[^a-z]', '', txt.lower()): returned2 = True
            c['second_login_failed_message'] = returned2
            vm.keys('ctrl', 'alt', 'f3'); time.sleep(3); vm.shot('tty3-again')
            got2, block2, owner2, _ = collect('S2', full=True)
            new_pids = {p[1] for p in owner2 if p[2] == 'plasmashell'} - first_pids
            c['first_session_ended'] = not ({p[1] for p in owner2} & first_pids)
            c['second_login_plasmashell'] = bool(new_pids) and not returned2
            (a.out / 'guest-facts-second-login.txt').write_text(block2)
        vm.keys('ctrl', 'alt', 'f1'); time.sleep(3); vm.shot('back-to-vt1')
        vm.keys('ctrl', 'alt', 'f2'); time.sleep(3); vm.shot('vt2')
    except Exception as e:
        result['error'] = str(e); vm.note('ERROR ' + str(e))
    finally:
        vm.stop(); del pw
        result['frames'] = vm.frames; result['timeline'] = vm.log
        c = result['checks']
        result['desktop_pass'] = bool(c.get('plasmashell_running') and c.get('kwin_running_for_owner')
                                      and not c.get('greeter_returned_after_login'))
        result['second_login_pass'] = bool(c.get('second_login_plasmashell'))
        result['orez_look_pass'] = bool(c.get('orez_defaults_in_session') and c.get('orez_wallpaper'))
        (a.out / 'vm-result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k: v for k, v in result.items() if k != 'frames'}, indent=2))
    return 0 if result['desktop_pass'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--ram', type=int, default=6144); p.add_argument('--cpus', type=int, default=4)
    p.add_argument('--desktop-wait', type=int, default=150)
    sys.exit(main(p.parse_args()))
