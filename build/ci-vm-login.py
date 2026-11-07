#!/usr/bin/env python3
"""Disposable UEFI VM test of the OREZ live login, driven through QEMU's QMP.

Diskless, offline guest; a random throwaway password created per run and never
written to evidence. Default GRUB entry, no edited kernel flags. Every frame is
kept (PNG). The verdict comes from in-guest facts written to the serial port
(loginctl / process list / journal), not from "screen looks non-blank".
"""
import argparse, json, os, random, socket, string, subprocess, sys, tempfile, time
from pathlib import Path

KEY = {c: c for c in string.ascii_lowercase + string.digits}
KEY.update({' ': 'spc', '-': 'minus', '=': 'equal', '.': 'dot', ',': 'comma', '/': 'slash', ';': 'semicolon',
            "'": 'apostrophe', '\n': 'ret', '\t': 'tab', '[': 'bracket_left', ']': 'bracket_right', '\\': 'backslash'})
SHIFT = {'_': 'minus', '+': 'equal', '>': 'dot', '<': 'comma', '?': 'slash', ':': 'semicolon', '"': 'apostrophe',
         '|': 'backslash', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8',
         '(': '9', ')': '0', '{': 'bracket_left', '}': 'bracket_right', '~': 'grave_accent'}


class VM:
    def __init__(self, iso, out, ram, cpus):
        self.out = out; self.frames = []; self.t0 = time.time(); self.log = []
        self.tmp = Path(tempfile.mkdtemp(prefix='orez-vm-'))
        code = next(p for p in ['/usr/share/OVMF/OVMF_CODE_4M.fd', '/usr/share/OVMF/OVMF_CODE.fd'] if os.path.exists(p))
        vars_ = code.replace('CODE', 'VARS'); subprocess.run(['cp', vars_, self.tmp / 'vars.fd'], check=True)
        accel = 'kvm' if os.access('/dev/kvm', os.W_OK) else 'tcg'
        self.note('accelerator=' + accel)
        self.proc = subprocess.Popen([
            'qemu-system-x86_64', '-machine', 'q35,accel=' + accel, '-cpu', 'host' if accel == 'kvm' else 'max',
            '-m', str(ram), '-smp', str(cpus),
            '-drive', f'if=pflash,format=raw,unit=0,readonly=on,file={code}',
            '-drive', f'if=pflash,format=raw,unit=1,file={self.tmp}/vars.fd',
            '-drive', f'if=none,id=cd,media=cdrom,format=raw,readonly=on,file={iso}',
            '-device', 'ahci,id=ahci', '-device', 'ide-cd,drive=cd,bus=ahci.0', '-boot', 'order=d',
            '-device', 'virtio-vga', '-display', 'none', '-usb', '-device', 'usb-tablet',
            '-qmp', f'unix:{self.tmp}/qmp.sock,server=on,wait=off',
            '-serial', f'file:{out}/serial.log', '-nic', 'none', '-no-reboot'])
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
        txt = subprocess.run(['tesseract', str(p), '-', '--psm', '3'], capture_output=True, text=True).stdout
        return p, txt

    def wait_text(self, words, label, timeout, every=5):
        end = time.time() + timeout
        while time.time() < end:
            if self.proc.poll() is not None: raise RuntimeError('guest stopped')
            _, txt = self.shot(label); low = txt.lower()
            hit = [w for w in words if w.lower() in low]
            if hit: self.note(f'{label}: saw {hit[0]!r}'); return hit[0]
            time.sleep(every)
        self.note(f'{label}: timeout waiting for {words}'); return None

    def serial(self):
        return (self.out / 'serial.log').read_text(errors='replace')

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
        seen = vm.wait_text(['New live-session password'], 'enroll', 900)
        result['checks']['enrollment_prompt'] = bool(seen)
        if not seen: raise RuntimeError('no enrollment prompt')
        vm.type(pw + '\n'); time.sleep(2); vm.shot('after-first-entry')
        vm.type(pw + '\n'); time.sleep(2)
        result['checks']['greeter'] = bool(vm.wait_text(['Welcome home', 'Your workspace'], 'greeter', 600))
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
        facts = ("sudo sh -c '{ echo ==OREZ-FACTS-BEGIN==; loginctl list-sessions --no-legend; "
                 "echo ==PROCS; ps -eo user,pid,comm | grep -E \"kwin|plasmashell|startplasma|ksmserver|dbus-run\"; "
                 "echo ==TRACE; journalctl -b --no-pager -o short-precise -t orez-session-trace; "
                 "echo ==SDDM; journalctl -b --no-pager -o short-precise -u sddm | tail -80; "
                 "echo ==SESSIONLOG; cat /home/orez/.local/share/sddm/wayland-session.log 2>&1 | tail -150; "
                 "echo ==USERJOURNAL; journalctl -b --no-pager -o short-precise _UID=1000 | tail -300; "
                 "echo ==COREDUMPS; coredumpctl list --no-pager 2>&1 | tail -20; "
                 "echo ==OREZ-FACTS-END==; } > /dev/ttyS0 2>&1'")
        got = vm.run_on_tty(pw, facts, '==OREZ-FACTS-END==', 90)
        result['checks']['facts_collected'] = got
        ser = vm.serial(); block = ser.split('==OREZ-FACTS-BEGIN==')[-1].split('==OREZ-FACTS-END==')[0] if got else ''
        procs = block.split('==PROCS')[-1].split('==TRACE')[0] if got else ''
        result['checks']['plasmashell_running'] = 'plasmashell' in procs
        result['checks']['kwin_running_for_owner'] = any(l.startswith('orez') and 'kwin' in l for l in procs.splitlines())
        (a.out / 'guest-facts.txt').write_text(block)
        vm.keys('ctrl', 'alt', 'f1'); time.sleep(3); vm.shot('back-to-vt1')
        vm.keys('ctrl', 'alt', 'f2'); time.sleep(3); vm.shot('vt2')
    except Exception as e:
        result['error'] = str(e); vm.note('ERROR ' + str(e))
    finally:
        vm.stop(); del pw
        result['frames'] = vm.frames; result['timeline'] = vm.log
        result['desktop_pass'] = bool(result['checks'].get('plasmashell_running') and not result['checks'].get('greeter_returned_after_login'))
        (a.out / 'vm-result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k: v for k, v in result.items() if k != 'frames'}, indent=2))
    return 0 if result['desktop_pass'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--ram', type=int, default=6144); p.add_argument('--cpus', type=int, default=4)
    p.add_argument('--desktop-wait', type=int, default=150)
    sys.exit(main(p.parse_args()))
