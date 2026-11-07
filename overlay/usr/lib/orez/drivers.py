#!/usr/bin/env python3
"""OREZ Drivers — one-click NVIDIA driver setup using Ubuntu's own tool.

Detection reads /sys only. Installation runs `pkexec ubuntu-drivers install`
(Canonical-signed modules for the running kernel; Secure Boot stays on), so the
owner's password is always required. Nothing is installed without consent.
`--check` prints the status for scripts; `--at-login` shows the offer only when
an NVIDIA GPU is present, its driver is not in use, and the owner has not
chosen "Don't ask again" (Settings → OREZ Drivers can always reopen it).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PCI = Path('/sys/bus/pci/devices')
DISMISS = Path.home() / '.config' / 'orez-drivers.json'


def nvidia_gpus(pci: Path = PCI) -> list[str]:
    found = []
    for dev in sorted(pci.glob('*')) if pci.is_dir() else []:
        try:
            vendor = (dev / 'vendor').read_text().strip()
            cls = (dev / 'class').read_text().strip()
        except OSError:
            continue
        if vendor == '0x10de' and cls.startswith('0x03'):
            found.append(dev.name)
    return found


def driver_in_use(pci: Path = PCI) -> str | None:
    for name in nvidia_gpus(pci):
        link = pci / name / 'driver'
        if link.is_symlink():
            return Path(link.resolve()).name
    return None


def status(pci: Path = PCI) -> dict:
    gpus = nvidia_gpus(pci)
    drv = driver_in_use(pci)
    return {'nvidia_gpu': bool(gpus), 'devices': gpus, 'driver': drv,
            'needs_setup': bool(gpus) and drv != 'nvidia'}


def dismissed() -> bool:
    try:
        return bool(json.loads(DISMISS.read_text()).get('dont_ask'))
    except (OSError, ValueError):
        return False


def main(argv):
    st = status()
    if '--check' in argv:
        print(json.dumps(st)); return 0
    if '--at-login' in argv and (not st['needs_setup'] or dismissed()):
        return 0
    from PySide6.QtWidgets import QApplication, QMessageBox
    app = QApplication(argv)
    if not st['nvidia_gpu']:
        QMessageBox.information(None, 'OREZ Drivers', 'No NVIDIA graphics card was found. Nothing to install.'); return 0
    if not st['needs_setup']:
        QMessageBox.information(None, 'OREZ Drivers', 'The NVIDIA driver is installed and in use.'); return 0
    box = QMessageBox(QMessageBox.Question, 'Install NVIDIA graphics driver?',
                      'Your NVIDIA card is using a basic driver ('
                      + (st['driver'] or 'none') + ').\n\nInstall the official NVIDIA driver from Ubuntu? '
                      'It is signed by Canonical, so Secure Boot stays on. You will be asked for your password, '
                      'and a restart is needed afterwards.')
    install = box.addButton('Install driver', QMessageBox.AcceptRole)
    box.addButton('Not now', QMessageBox.RejectRole)
    never = box.addButton("Don't ask again", QMessageBox.DestructiveRole)
    box.exec()
    if box.clickedButton() is never:
        DISMISS.parent.mkdir(parents=True, exist_ok=True); DISMISS.write_text('{"dont_ask": true}\n'); return 0
    if box.clickedButton() is not install:
        return 0
    result = subprocess.run(['pkexec', 'ubuntu-drivers', 'install'], capture_output=True, text=True)
    if result.returncode == 0:
        QMessageBox.information(None, 'OREZ Drivers', 'Driver installed. Restart OREZ to start using it.')
        return 0
    QMessageBox.warning(None, 'OREZ Drivers', 'The driver was not installed.\n\n' + (result.stderr or '')[-800:])
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
