#!/usr/bin/env python3
"""Capture an ordinary-user, diskless, offline UEFI boot of an exact live ISO.

QMP is a private local test console. This harness never enters credentials or
declares desktop success from a nonblank screen. Human inspection is required.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('probe', ROOT / 'build/probe-virgl-vm.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iso', type=Path, required=True)
    p.add_argument('--sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seconds', type=int, default=1200)
    a = p.parse_args()
    if os.geteuid() == 0 or not 30 <= a.seconds <= 3600:
        p.error('Require an ordinary user and a 30..3600 second observation window')
    if a.iso.is_symlink() or not stat.S_ISREG(a.iso.stat().st_mode):
        p.error('ISO must be a regular file')
    if any(',' in str(path) for path in [a.iso, a.output]):
        p.error('Commas in QEMU paths are unsupported')
    with a.iso.open('rb') as f:
        actual = hashlib.file_digest(f, 'sha256').hexdigest()
    if actual != a.sha256:
        p.error('ISO digest mismatch')
    os.umask(0o022)
    a.output.mkdir(parents=True, exist_ok=False)
    firmware = Path('/usr/share/OVMF/OVMF_CODE_4M.fd')
    variables = Path('/usr/share/OVMF/OVMF_VARS_4M.fd')
    record = {'schema': 1, 'iso_sha256': actual, 'guest_ram_mib': 6144,
              'acceleration': 'tcg', 'graphics': 'virtio-vga (2D)',
              'network': 'none', 'writable_disks': [], 'host_devices': [],
              'secure_boot_tested': False, 'desktop_verified': False,
              'installation_approved': False, 'frames': [],
              'firmware_sha256': hashlib.sha256(firmware.read_bytes()).hexdigest()}
    process = None
    from PIL import Image
    try:
        with tempfile.TemporaryDirectory(prefix='orez-qmp-') as temp:
            runtime = Path(temp)
            shutil.copyfile(variables, runtime / 'vars.fd')
            (a.output / 'console-path.txt').write_text(str(runtime / 'qmp.sock') + '\n')
            command = ['qemu-system-x86_64', '-machine', 'q35,accel=tcg', '-cpu', 'max',
                       '-m', '6144', '-smp', '2', '-vga', 'none', '-device', 'virtio-vga',
                       '-display', 'none', '-nic', 'none', '-monitor', 'none',
                       '-qmp', f'unix:{runtime}/qmp.sock,server=on,wait=off',
                       '-serial', f'file:{a.output}/serial.log', '-no-reboot',
                       '-device', 'qemu-xhci,id=orez-xhci', '-device', 'usb-tablet,bus=orez-xhci.0',
                       '-drive', f'file={a.iso},if=ide,index=1,media=cdrom,format=raw,readonly=on',
                       '-drive', f'if=pflash,format=raw,unit=0,readonly=on,file={firmware}',
                       '-drive', f'if=pflash,format=raw,unit=1,file={runtime}/vars.fd',
                       '-boot', 'order=d']
            record['command'] = command
            with (a.output / 'qemu.log').open('w') as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                started = time.monotonic()
                while not (runtime / 'qmp.sock').exists():
                    if process.poll() is not None or time.monotonic() - started > 20:
                        raise RuntimeError('QEMU did not start')
                    time.sleep(.2)
                os.chmod(runtime / 'qmp.sock', 0o600)
                next_frame = 5
                while time.monotonic() - started < a.seconds:
                    if (a.output / 'stop-requested').exists():
                        record['stop_reason'] = 'operator ended observation'
                        break
                    if process.poll() is not None:
                        raise RuntimeError('QEMU exited unexpectedly')
                    elapsed = int(time.monotonic() - started)
                    if elapsed < next_frame:
                        time.sleep(1)
                        continue
                    next_frame = elapsed + 30
                    ppm = a.output / f'guest-{elapsed:04d}.ppm'
                    qmp = None
                    try:
                        qmp = helper.QMP(runtime / 'qmp.sock')
                        qmp.call('screendump', {'filename': str(ppm)})
                        with Image.open(ppm) as frame:
                            frame.save(ppm.with_suffix('.png'))
                        record['frames'].append(ppm.with_suffix('.png').name)
                        print('Captured actual UEFI guest frame:', elapsed, flush=True)
                    except helper.QMPCommandError as error:
                        record.setdefault('frame_errors', []).append({'seconds': elapsed, 'error': str(error)})
                    finally:
                        if qmp:
                            qmp.close()
                        ppm.unlink(missing_ok=True)
                    (a.output / 'boot-observation.json').write_text(json.dumps(record, indent=2) + '\n')
    finally:
        helper.stop(process)
        (a.output / 'boot-observation.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Capture completed. Login, desktop and installation remain unqualified until reviewed.')


if __name__ == '__main__':
    main()
