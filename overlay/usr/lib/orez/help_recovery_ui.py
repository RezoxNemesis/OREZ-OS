#!/usr/bin/env python3
"""OREZ Help & Recovery: honest guidance and read-only local diagnostics."""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

def read_os():
    values = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value.strip().strip('"')
    except OSError:
        pass
    return values

def safe_command(args: list[str], timeout: int = 4) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                                check=False, env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
        if result.returncode == 0:
            return result.stdout.strip() or "Available; no additional details."
        return "Not available in this session."
    except (OSError, subprocess.SubprocessError):
        return "Not available in this session."

def diagnostics() -> dict:
    os_info = read_os()
    root = shutil.disk_usage("/")
    mem = "Not available"
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                mem = f"{int(line.split()[1]) // 1024} MiB visible"
                break
    except (OSError, ValueError, IndexError):
        pass
    boot = "UEFI" if Path("/sys/firmware/efi").is_dir() else "Legacy / virtual / unknown"
    failed = safe_command(["systemctl", "--failed", "--no-legend", "--plain"])
    return {
        "OREZ Help & Recovery diagnostic": {
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "os": os_info.get("PRETTY_NAME", "Linux (distribution not identified)"),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "boot_mode": boot,
            "memory": mem,
            "root_filesystem_free_gib": round(root.free / (1024 ** 3), 2),
            "failed_system_units": failed,
            "privacy": "No username, serial number, IP address, Wi-Fi names, saved passwords, file names or personal logs are collected.",
        }
    }

class HelpWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OREZ Help & Recovery")
        self.resize(900, 680)
        self.setMinimumSize(760, 560)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(26, 22, 26, 24)
        layout.setSpacing(14)
        heading = QLabel("Help & Recovery")
        heading.setStyleSheet("font-size:28px;font-weight:650")
        subtitle = QLabel("Clear next steps, honest system status, and safe diagnostics.")
        subtitle.setStyleSheet("color:#595959")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.make_help(), "Get help")
        self.tabs.addTab(self.make_recovery(), "Recovery status")
        self.tabs.addTab(self.make_diagnostics(), "System check")
        layout.addWidget(self.tabs, 1)

        footer = QHBoxLayout()
        home = QPushButton("Back to Settings")
        home.clicked.connect(lambda: self.open_app(["systemsettings"]))
        footer.addWidget(home)
        files = QPushButton("Open Files")
        files.clicked.connect(lambda: self.open_app(["dolphin"]))
        footer.addWidget(files)
        footer.addStretch(1)
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        footer.addWidget(close)
        layout.addLayout(footer)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow,QWidget{background:#f6f4ef;color:#161616}
            QTabWidget::pane{background:#fff;border:1px solid #dedad1;border-radius:12px}
            QTabBar::tab{padding:11px 18px;background:#ece9e2;border-radius:8px;margin-right:4px}
            QTabBar::tab:selected{background:#fff}
            QTextEdit{background:#fff;border:0;padding:16px;font-size:14px}
            QPushButton{background:#242424;color:#fff;border:0;border-radius:9px;padding:10px 15px}
            QPushButton:hover{background:#444}
        """)

    def page(self, text: str) -> QTextEdit:
        view = QTextEdit()
        view.setReadOnly(True)
        view.setPlainText(text)
        view.setAccessibleName("OREZ help information")
        return view

    def make_help(self):
        return self.page(
            "START HERE\n\n"
            "If an app window is stuck, wait briefly, then close only that app. "
            "Your files are not automatically deleted when an app closes.\n\n"
            "If the desktop is still responding, open Settings from the taskbar or use Back to Settings below. "
            "Use Files to find documents and removable drives. Do not choose Format or Erase unless you deliberately intend to erase a drive.\n\n"
            "If the screen is blank or the desktop does not appear, do not repeatedly change graphics drivers or boot settings. "
            "Restart the computer and choose the normal OREZ live entry again. This development build has a known graphical sign-in issue; "
            "a successful password prompt does not yet guarantee the desktop will start.\n\n"
            "If you cannot sign in, check the keyboard layout and Caps Lock. Do not share your password with support. "
            "This build does not provide a supported graphical login repair yet.\n\n"
            "For project status and known limitations, visit github.com/RezoxNemesis/OREZ-OS."
        )

    def make_recovery(self):
        return self.page(
            "RECOVERY CAPABILITIES — DEVELOPMENT BUILD\n\n"
            "System restore: NOT AVAILABLE. No qualified restore-point workflow is installed.\n\n"
            "Automatic rollback: NOT AVAILABLE. Package or graphics-driver rollback has not been qualified.\n\n"
            "Backup restore: NOT AVAILABLE. No backup is created or restored by this screen. Keep independent copies of important files.\n\n"
            "OS installer: DISABLED. This live candidate is not approved for installation.\n\n"
            "Disk protection: This screen never formats, partitions, mounts, repairs or writes to disks.\n\n"
            "SAFE NEXT STEP\n"
            "If important files are on a drive, stop before attempting repairs or reinstalling. Use a separate trusted system or qualified technician to copy and verify your files first. "
            "Never use the Windows recovery USB as OREZ installation media.\n\n"
            "These unavailable capabilities will remain clearly labelled until they pass disposable-disk tests."
        )

    def make_diagnostics(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        note = QLabel("Read-only checks only. This report avoids personal identifiers and does not change system settings.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.report.setAccessibleName("Read-only system diagnostic report")
        self.refresh_report()
        layout.addWidget(self.report, 1)
        actions = QHBoxLayout()
        refresh = QPushButton("Refresh checks")
        refresh.clicked.connect(self.refresh_report)
        actions.addWidget(refresh)
        export = QPushButton("Save diagnostic report")
        export.clicked.connect(self.export_report)
        actions.addWidget(export)
        actions.addStretch(1)
        layout.addLayout(actions)
        return page

    def refresh_report(self):
        self.report_data = diagnostics()
        self.report.setPlainText(json.dumps(self.report_data, indent=2, ensure_ascii=False))

    def export_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save diagnostic report",
            str(Path.home() / "orez-diagnostic-report.json"), "JSON files (*.json)")
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self.report_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except OSError as error:
            QMessageBox.warning(self, "Could not save report", f"No system settings were changed.\n\n{error}")

    def open_app(self, args):
        try:
            subprocess.Popen(args, close_fds=True)
        except OSError as error:
            QMessageBox.warning(self, "Application unavailable", f"OREZ could not open this application. No settings were changed.\n\n{error.strerror or 'Application not installed.'}")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("OREZ Help & Recovery")
    window = HelpWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
