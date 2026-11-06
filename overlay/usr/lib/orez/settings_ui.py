#!/usr/bin/env python3
"""Searchable, beginner-friendly OREZ settings front door.

This application is a navigation layer over the installed native KDE controls.
It does not keep shadow settings, elevate privileges, or execute shell strings.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

CATALOG = Path("/usr/share/orez/settings-catalog.json")
ALLOWED_ACTIONS = {
    "system-settings": ["systemsettings"],
    "network": ["systemsettings", "kcm_networkmanagement"],
    "bluetooth": ["systemsettings", "kcm_bluetooth"],
    "power": ["systemsettings", "kcm_powerdevil"],
    "files": ["dolphin"],
    "apps": ["orez-store", "gui"],
    "connect": ["orezctl", "connect", "open"],
    "help": ["orez-help"],
}


def load_catalog(path: Path = CATALOG) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("categories"), list):
        raise ValueError("The OREZ Settings catalogue has an unsupported format.")
    for category in data["categories"]:
        if not category.get("title") or not isinstance(category.get("items"), list):
            raise ValueError("A Settings category is incomplete.")
        for item in category["items"]:
            if item.get("action") not in ALLOWED_ACTIONS:
                raise ValueError("A Settings action is not allowlisted.")
            if not item.get("title") or not item.get("description"):
                raise ValueError("A Settings item is missing its explanation.")
    return data


class SettingsWindow(QMainWindow):
    def __init__(self, catalog: dict):
        super().__init__()
        self.catalog = catalog
        self.active_category = "All settings"
        self.setWindowTitle("OREZ Settings")
        self.setMinimumSize(900, 620)
        self.resize(1080, 720)
        self.setAccessibleName("OREZ Settings")

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(28, 24, 28, 22)
        root_layout.setSpacing(16)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        subtitle = QLabel("One clear place to find and change how your computer works.")
        subtitle.setObjectName("muted")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)
        home = QPushButton("Home")
        home.setAccessibleName("Return to all Settings")
        home.clicked.connect(self.show_home)
        header.addWidget(home)
        help_button = QPushButton("Help & Recovery")
        help_button.clicked.connect(lambda: self.launch("help"))
        header.addWidget(help_button)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        header.addWidget(close_button)
        root_layout.addLayout(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search Wi-Fi, Bluetooth, display, password, updates, backup…")
        self.search.setClearButtonEnabled(True)
        self.search.setAccessibleName("Search Settings")
        self.search.textChanged.connect(self.render_items)
        root_layout.addWidget(self.search)

        body = QHBoxLayout()
        self.navigation = QListWidget()
        self.navigation.setFixedWidth(245)
        self.navigation.setAccessibleName("Settings categories")
        self.navigation.addItem(QListWidgetItem("All settings"))
        for category in self.catalog["categories"]:
            self.navigation.addItem(QListWidgetItem(category["title"]))
        self.navigation.currentTextChanged.connect(self.change_category)
        body.addWidget(self.navigation)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.cards = QWidget()
        self.cards_layout = QVBoxLayout(self.cards)
        self.cards_layout.setContentsMargins(8, 2, 8, 8)
        self.cards_layout.setSpacing(12)
        self.scroll.setWidget(self.cards)
        body.addWidget(self.scroll, 1)
        root_layout.addLayout(body, 1)

        footer = QLabel("OREZ keeps native Linux controls available. Advanced tools remain optional.")
        footer.setObjectName("muted")
        root_layout.addWidget(footer)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #F6F4EF; color: #161616; }
            QLabel#pageTitle { font-size: 28px; font-weight: 650; }
            QLabel#muted { color: #595959; }
            QLineEdit { background: #FFFFFF; border: 1px solid #C9C5BC; border-radius: 12px; padding: 12px 14px; font-size: 15px; }
            QListWidget { background: #EEECE6; border: 0; border-radius: 14px; padding: 8px; }
            QListWidget::item { padding: 12px 10px; border-radius: 8px; }
            QListWidget::item:selected { background: #DCD8CE; color: #161616; }
            QFrame#settingCard { background: #FFFFFF; border: 1px solid #DEDAD1; border-radius: 14px; }
            QPushButton { background: #242424; color: #FFFFFF; border: 0; border-radius: 10px; padding: 10px 15px; }
            QPushButton:hover { background: #444444; }
            QPushButton:focus, QLineEdit:focus, QListWidget:focus { outline: 2px solid #555555; border: 2px solid #555555; }
        """)
        self.navigation.setCurrentRow(0)
        self.render_items()

    def show_home(self):
        self.search.clear()
        self.navigation.setCurrentRow(0)
        self.active_category = "All settings"
        self.render_items()

    def change_category(self, name: str):
        if name:
            self.active_category = name
            self.render_items()

    def render_items(self, _query: str = ""):
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()
        query = self.search.text().casefold().strip()
        found = 0
        for category in self.catalog["categories"]:
            if self.active_category not in ("All settings", category["title"]):
                continue
            for item in category["items"]:
                searchable = " ".join([
                    category["title"], item["title"], item["description"],
                    " ".join(item.get("keywords", [])),
                ]).casefold()
                if query and query not in searchable:
                    continue
                card = QFrame()
                card.setObjectName("settingCard")
                row = QHBoxLayout(card)
                copy = QVBoxLayout()
                name = QLabel(item["title"])
                name.setFont(QFont("", 12, QFont.Weight.DemiBold))
                description = QLabel(item["description"])
                description.setWordWrap(True)
                description.setObjectName("muted")
                copy.addWidget(name)
                copy.addWidget(description)
                row.addLayout(copy, 1)
                action = QPushButton(item.get("button", "Open"))
                action.clicked.connect(lambda _checked=False, key=item["action"]: self.launch(key))
                row.addWidget(action)
                self.cards_layout.addWidget(card)
                found += 1
        if not found:
            empty = QLabel("No matching setting. Try a simpler word, or choose All settings.")
            empty.setObjectName("muted")
            empty.setWordWrap(True)
            self.cards_layout.addWidget(empty)
        self.cards_layout.addStretch(1)

    def launch(self, action: str):
        command = ALLOWED_ACTIONS.get(action)
        if not command:
            QMessageBox.warning(self, "Not available", "This action is not available in this OREZ build.")
            return
        try:
            subprocess.Popen(command, close_fds=True)
        except OSError as error:
            QMessageBox.warning(
                self, "Could not open this setting",
                f"OREZ could not open this screen. Your settings have not been changed.\n\n{error.strerror or 'The application is unavailable.'}",
            )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OREZ Settings")
    try:
        catalog = load_catalog()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        QMessageBox.critical(None, "OREZ Settings unavailable", f"Settings could not be loaded. No system changes were made.\n\n{error}")
        return 1
    window = SettingsWindow(catalog)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
