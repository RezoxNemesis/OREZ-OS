#!/usr/bin/env python3
"""Diskless, offline live-ISO diagnostic with software-backed virtual OpenGL.

This is a development harness, never an installed service. It uses a normal
user's Xvfb and QEMU SDL display, TCG and llvmpipe. Captured nonblank frames do
not certify a desktop, hardware acceleration, Secure Boot or installation.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]


def load_helper(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QMP:
    def __init__(self, path):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(12)
        self.socket.connect(str(path))
        self.stream = self.socket.makefile('rwb')
        self.greeting = json.loads(self.stream.readline())
        self.call('qmp_capabilities')

    def call(self, command, arguments=None):
        message = {'execute': command}
        if arguments is not None:
            message['arguments'] = arguments
        self.stream.write(json.dumps(message).encode() + b'\n')
        self.stream.flush()
        while True:
            line = self.stream.readline()
            if not line:
                raise RuntimeError('QMP disconnected')
            result = json.loads(line)
            if 'error' in result:
                raise RuntimeError(result['error'])
            if 'return' in result:
                return result['return']

    def close(self):
        self.stream.close()
        self.socket.close()


def command(iso, output, runtime, boot, firmware=None, ram=4096):
    # Explicit configuration: no block-device passthrough, writable disk, NIC,
    # shared folder, VNC server, host keyboard or host administrator privilege.
    args = ['qemu-system-x86_64', '-machine', 'q35,accel=tcg', '-cpu', 'max',
            '-m', str(ram), '-smp', '2', '-vga', 'none', '-device', 'virtio-vga-gl',
            '-display', 'sdl,gl=on', '-nic', 'none', '-monitor', 'none',
            '-qmp', f'unix:{runtime}/qmp.sock,server=on,wait=off',
            '-serial', f'file:{output}/serial.log', '-no-reboot',
            '-device', 'qemu-xhci,id=orez-xhci', '-device', 'usb-tablet,bus=orez-xhci.0',
            '-drive', f'file={iso},if=ide,index=1,media=cdrom,format=raw,readonly=on']
    if boot == 'direct':
        args += ['-kernel', str(output / 'vmlinuz'), '-initrd', str(output / 'initrd'),
                 '-append', 'boot=casper orez.verify=1 console=ttyS0,115200n8 loglevel=4 systemd.show_status=1']
    else:
        args += ['-drive', f'if=pflash,format=raw,unit=0,readonly=on,file={firmware}',
                 '-drive', f'if=pflash,format=raw,unit=1,file={runtime}/vars.fd',
                 '-boot', 'order=d']
    return args


def stop(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--boot', choices=['direct', 'uefi'], required=True)
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--ram-mib', type=int, choices=[4096, 6144], default=4096)
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('run QEMU as an ordinary user, never root')
    if not 30 <= args.seconds <= 1200:
        parser.error('seconds must be 30..1200')
    iso, output = args.iso.resolve(), args.output.resolve()
    if not stat.S_ISREG(iso.stat().st_mode) or ',' in str(iso):
        parser.error('ISO must be a regular file without commas in its path')
    if ',' in str(output):
        parser.error('output path must not contain commas')
    if len(args.sha256) != 64 or any(c not in '0123456789abcdef' for c in args.sha256):
        parser.error('provide the expected lowercase SHA-256')
    for tool in ['qemu-system-x86_64', 'Xvfb', 'glxinfo', 'scrot', 'xorriso']:
        if not shutil.which(tool):
            parser.error(f'missing dependency: {tool}')
    from PIL import Image
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {'schema_version': 1, 'boot': args.boot, 'iso': str(iso),
              'expected_sha256': args.sha256, 'guest_ram_mib': args.ram_mib,
              'cpu_accelerator': 'tcg', 'host_renderer': 'llvmpipe',
              'device': 'virtio-vga-gl', 'network': 'none', 'writable_disks': [],
              'installation_approved': False, 'desktop_qualified': False,
              'secure_boot_tested': False, 'frames': []}
    xserver = qemu = qmp = None
    try:
        with iso.open('rb') as stream:
            report['actual_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        if report['actual_sha256'] != args.sha256:
            raise RuntimeError('ISO digest mismatch; refusing boot')
        if args.boot == 'direct':
            for name in ['vmlinuz', 'initrd']:
                subprocess.run(['xorriso', '-osirrox', 'on', '-indev', str(iso),
                                '-extract', f'/casper/{name}', str(output / name)],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with tempfile.TemporaryDirectory(prefix='orez-virgl-') as temp:
            runtime = Path(temp)
            environment = {**os.environ, 'LIBGL_ALWAYS_SOFTWARE': '1',
                           'GALLIUM_DRIVER': 'llvmpipe', 'SDL_VIDEODRIVER': 'x11',
                           'XDG_RUNTIME_DIR': str(runtime)}
            firmware = None
            if args.boot == 'uefi':
                firmware = Path('/usr/share/OVMF/OVMF_CODE_4M.fd')
                variables = Path('/usr/share/OVMF/OVMF_VARS_4M.fd')
                shutil.copyfile(variables, runtime / 'vars.fd')
                report['firmware_sha256'] = hashlib.sha256(firmware.read_bytes()).hexdigest()
                report['initial_vars_sha256'] = hashlib.sha256(variables.read_bytes()).hexdigest()
            with (output / 'xvfb.log').open('w') as xlog, (output / 'qemu.log').open('w') as qlog:
                read_fd, write_fd = os.pipe()
                try:
                    xserver = subprocess.Popen(['Xvfb', '-displayfd', str(write_fd),
                        '-screen', '0', '1440x1000x24', '-nolisten', 'tcp'],
                        pass_fds=(write_fd,), stdout=xlog, stderr=subprocess.STDOUT)
                    os.close(write_fd)
                    write_fd = None
                    if not select.select([read_fd], [], [], 15)[0]:
                        raise RuntimeError('Xvfb did not become ready')
                    display = os.read(read_fd, 32).decode().strip()
                    if not display.isdecimal():
                        raise RuntimeError('Xvfb returned invalid display')
                    environment['DISPLAY'] = ':' + display
                finally:
                    os.close(read_fd)
                    if write_fd is not None:
                        os.close(write_fd)
                gl = subprocess.run(['glxinfo', '-B'], env=environment, capture_output=True, text=True, timeout=30)
                (output / 'glxinfo.txt').write_text(gl.stdout + gl.stderr)
                gl.check_returncode()
                if 'llvmpipe' not in gl.stdout:
                    raise RuntimeError('requested software renderer not confirmed')
                invocation = command(iso, output, runtime, args.boot, firmware, args.ram_mib)
                report['command'] = invocation
                print(json.dumps(report), flush=True)
                qemu = subprocess.Popen(invocation, env=environment, stdout=qlog, stderr=subprocess.STDOUT)
                started = time.monotonic()
                while not (runtime / 'qmp.sock').exists():
                    if qemu.poll() is not None or time.monotonic() - started > 20:
                        raise RuntimeError('QEMU failed to expose its private QMP socket')
                    time.sleep(.2)
                qmp = QMP(runtime / 'qmp.sock')
                report['qemu'] = qmp.greeting
                frame_helper = load_helper('check-graphical-frame')
                next_frame = 10
                clicked = False
                while time.monotonic() - started < args.seconds:
                    if qemu.poll() is not None:
                        raise RuntimeError(f'QEMU exited unexpectedly: {qemu.returncode}')
                    elapsed = int(time.monotonic() - started)
                    if elapsed < next_frame:
                        time.sleep(1)
                        continue
                    next_frame = elapsed + 20
                    ppm = output / f'guest-{elapsed:04d}.ppm'
                    qmp.call('screendump', {'filename': str(ppm)})
                    Image.open(ppm).save(ppm.with_suffix('.png'))
                    subprocess.run(['scrot', str(output / f'host-window-{elapsed:04d}.png')],
                                   env=environment, check=True, timeout=15)
                    visible, details = frame_helper.inspect(ppm)
                    frame = {'seconds': elapsed, 'file': ppm.with_suffix('.png').name,
                             'nonblank': visible, 'details': details}
                    if not clicked:
                        prompt = subprocess.run([sys.executable, str(ROOT / 'build/check-try-frame.py'), str(ppm)],
                                                capture_output=True, text=True, timeout=10)
                        if prompt.returncode == 0:
                            # Only the known left Try button; never an unknown screen.
                            qmp.call('input-send-event', {'events': [
                                {'type': 'abs', 'data': {'axis': 'x', 'value': 8959}},
                                {'type': 'abs', 'data': {'axis': 'y', 'value': 26214}}]})
                            time.sleep(.4)
                            for down in (True, False):
                                qmp.call('input-send-event', {'events': [
                                    {'type': 'btn', 'data': {'button': 'left', 'down': down}}]})
                                time.sleep(.3)
                            clicked = True
                            report['try_clicked_at_seconds'] = elapsed
                            frame['action'] = 'known Try button clicked'
                    report['frames'].append(frame)
                    print(json.dumps(frame), flush=True)
                    ppm.unlink()
                    if (output / 'stop-requested').exists():
                        report['stop_reason'] = 'operator requested end of diagnostic'
                        break
                report['status'] = 'captured_requires_visual_review'
                report['try_clicked'] = clicked
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report.update(status='failed', error=str(error))
        print(f'FAIL: {error}', file=sys.stderr, flush=True)
    finally:
        if qmp:
            qmp.close()
        stop(qemu)
        stop(xserver)
        for name in ['vmlinuz', 'initrd']:
            (output / name).unlink(missing_ok=True)
        (output / 'vm-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Diagnostic only: inspect PNG frames. No automatic desktop or install qualification.', flush=True)
    return int(report['status'] == 'failed')


if __name__ == '__main__':
    sys.exit(main())
