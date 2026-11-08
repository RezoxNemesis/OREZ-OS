#!/usr/bin/env python3
"""OREZ Update — window for installing an OREZ update from a USB drive.

Runs as the signed-in owner. Installing is done by update_apply.py through
pkexec, so the owner's password is asked every time. Nothing runs in the
background and nothing is downloaded by this window itself.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import update_apply as core  # noqa: E402

from PySide6.QtCore import QProcess, Qt  # noqa: E402
from PySide6.QtGui import QFont, QIcon, QPixmap  # noqa: E402
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel, QMessageBox,  # noqa: E402
                               QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout, QWidget)

INK = '#1d1d1b'
PAPER = '#f4f1ea'


def applier() -> Path:
    # The installed OREZ copy is used once present; the first update runs the copy on the USB.
    installed = Path('/usr/lib/orez/update_apply.py')
    return HERE / 'update_apply.py' if HERE != installed.parent else installed


def overall(line: str, cur: int) -> int:
    m = re.match(r'STEP (\d+)/(\d+)', line)
    if m:
        return int((int(m.group(1)) - 1) * 100 / int(m.group(2)))
    m = re.match(r'COPY (\d+)', line)
    if m:
        return int(100 / 7 + int(m.group(1)) * (100 / 7) / 100)
    m = re.match(r'INSTALL (\d+)', line)
    if m:
        return int(4 * 100 / 7 + int(m.group(1)) * (100 / 7) / 100)
    return cur


class Window(QWidget):
    def __init__(self, media_arg: Path | None):
        super().__init__()
        self.setWindowTitle('OREZ Update')
        for icon in ('/usr/share/icons/hicolor/scalable/apps/orez-update.svg', '/usr/share/pixmaps/orez-logo.png'):
            if Path(icon).is_file():
                self.setWindowIcon(QIcon(icon)); break
        self.resize(760, 640)
        self.setStyleSheet(f'QWidget{{background:{PAPER};color:{INK};font-size:11pt}}'
                           f'QPushButton{{padding:10px 22px;border:1px solid {INK};border-radius:6px}}'
                           f'QPushButton#primary{{background:{INK};color:{PAPER}}}'
                           'QPushButton:disabled{color:#999;border-color:#bbb;background:#e6e2d9}'
                           'QPlainTextEdit{background:#fbfaf6;font-family:monospace;font-size:9pt}')
        self.media_arg = media_arg
        self.media: Path | None = None
        self.manifest: dict | None = None
        self.proc: QProcess | None = None
        lay = QVBoxLayout(self)
        head = QHBoxLayout()
        logo = QLabel()
        pm = QPixmap('/usr/share/pixmaps/orez-logo.png')
        if not pm.isNull():
            logo.setPixmap(pm.scaledToHeight(56, Qt.SmoothTransformation))
        head.addWidget(logo)
        self.title = QLabel('OREZ Update')
        f = QFont(); f.setPointSize(18); self.title.setFont(f)
        head.addWidget(self.title, 1)
        lay.addLayout(head)
        self.info = QLabel(); self.info.setWordWrap(True); self.info.setTextFormat(Qt.RichText)
        self.info.setOpenExternalLinks(True)
        lay.addWidget(self.info)
        self.nvidia = QCheckBox('Install the NVIDIA graphics driver (Canonical-signed, Secure Boot stays on)')
        lay.addWidget(self.nvidia)
        self.claude = QCheckBox('Install the Claude desktop app (official, from Anthropic)')
        self.claude.setChecked(True)
        lay.addWidget(self.claude)
        self.steam = QCheckBox('Install Steam for Windows games (Steam shows Valve\'s agreement when it first starts)')
        self.steam.setChecked(True)
        lay.addWidget(self.steam)
        link = QLabel(f'<a href="{core.STEAM_AGREEMENT}">Read the Steam Subscriber Agreement now</a>')
        link.setOpenExternalLinks(True)
        lay.addWidget(link)
        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.setValue(0)
        lay.addWidget(self.progress)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        lay.addWidget(self.log, 1)
        row = QHBoxLayout()
        self.rescan = QPushButton('Look for the USB again'); self.rescan.clicked.connect(self.scan)
        row.addWidget(self.rescan)
        row.addStretch(1)
        self.go = QPushButton('Install update'); self.go.setObjectName('primary'); self.go.clicked.connect(self.start)
        row.addWidget(self.go)
        self.restart = QPushButton('Restart now'); self.restart.setObjectName('primary'); self.restart.clicked.connect(self.reboot)
        self.restart.hide(); row.addWidget(self.restart)
        lay.addLayout(row)
        self.scan()

    def scan(self):
        found = [self.media_arg] if self.media_arg else core.find_media()
        if not self.media_arg and HERE.name == 'orez-update' and (HERE / 'update.json').is_file():
            found = [HERE] + [m for m in found if m.resolve() != HERE]
        self.media = self.manifest = None
        for m in found:
            try:
                self.manifest = core.load_manifest((m / 'update.json').read_text())
                self.media = m
                break
            except (OSError, ValueError, core.UpdateError):
                continue
        self.claude.setVisible(bool(self.manifest_claude()))
        gpu = core.nvidia_gpu()
        self.nvidia.setChecked(gpu); self.nvidia.setVisible(gpu)
        if not self.manifest:
            self.title.setText('OREZ Update')
            self.info.setText('Plug in the OREZ update USB, open it once in Dolphin (so it is mounted), '
                              'then press <b>Look for the USB again</b>.')
            self.go.setEnabled(False)
            return
        cur = core.current_version() or 'unknown'
        v = self.manifest['version']
        self.title.setText(f'OREZ OS {v} is ready to install')
        items = ''.join(f'<li>{x}</li>' for x in self.manifest['summary'])
        self.info.setText(f'This PC runs <b>OREZ OS {cur}</b>. The update on the USB brings:<ul>{items}</ul>'
                          'Everything is checked against Ubuntu&#39;s signatures and the update&#39;s checksums before '
                          'anything is installed. You will be asked for your password. Keep the PC plugged in.')
        self.go.setEnabled(True)
        self.log.setPlainText(f'Update found at {self.media}')

    def manifest_claude(self):
        return (self.manifest or {}).get('claude_packages') if self.manifest else True

    def start(self):
        if not self.media:
            return
        if not shutil.which('pkexec'):
            QMessageBox.warning(self, 'OREZ Update', 'pkexec is missing; cannot ask for administrator rights.'); return
        args = ['/usr/bin/python3', '-I', str(applier()), '--media', str(self.media)]
        if self.steam.isChecked():
            args.append('--accept-steam-license')
        if not self.claude.isChecked() or not self.manifest.get('claude_packages'):
            args.append('--no-claude')
        if self.nvidia.isVisible():
            args.append('--nvidia' if self.nvidia.isChecked() else '--no-nvidia')
        for w in (self.go, self.rescan, self.steam, self.nvidia, self.claude): w.setEnabled(False)
        self.log.appendPlainText('Starting… enter your password when asked.')
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.read)
        self.proc.finished.connect(self.done)
        self.proc.start('pkexec', args)

    def read(self):
        data = bytes(self.proc.readAllStandardOutput()).decode(errors='replace')
        for line in data.splitlines():
            self.progress.setValue(overall(line, self.progress.value()))
            if line.startswith('COPY '):
                continue
            if line.startswith('INSTALL '):
                parts = line.split(maxsplit=2)
                line = '  set up ' + (parts[2] if len(parts) > 2 else '')
            elif line.startswith('STEP '):
                line = '\n▸ ' + line.split(' ', 2)[2]
            self.log.appendPlainText(line)

    def done(self, code, _status):
        text = self.log.toPlainText()
        if code == 0 and 'DONE ' in text:
            self.progress.setValue(100)
            self.title.setText('Update installed — restart to finish')
            self.restart.show(); self.go.hide()
        else:
            self.title.setText('The update was not completed')
            if code in (126, 127):
                self.log.appendPlainText('Administrator password was not given; nothing was changed.')
            for w in (self.go, self.rescan, self.steam, self.nvidia, self.claude): w.setEnabled(True)

    def reboot(self):
        if subprocess.run(['qdbus6', 'org.kde.Shutdown', '/Shutdown', 'logoutAndReboot']).returncode != 0:
            subprocess.run(['systemctl', 'reboot'])


def main(argv):
    media = None
    if len(argv) > 2 and argv[1] == '--media':
        media = Path(argv[2])
    app = QApplication(argv)
    app.setApplicationName('OREZ Update'); app.setDesktopFileName('orez-update')
    w = Window(media); w.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
