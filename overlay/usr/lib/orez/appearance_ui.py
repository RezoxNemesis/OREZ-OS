#!/usr/bin/env python3
"""OREZ Appearance — see a choice before you keep it.

Five simple groups. Each choice shows a preview: the real wallpaper, the real
colour scheme rendered with Qt, or a screenshot captured from an actual OREZ
VM boot when one is packaged. "Try it" applies the choice to your real desktop
for 20 seconds and puts everything back unless you press Keep.
"""
from __future__ import annotations

import configparser
import sys
from pathlib import Path

sys.path.insert(0, '/usr/lib/orez')
import appearance_model as model  # noqa: E402

from PySide6.QtCore import Qt, QTimer  # noqa: E402
from PySide6.QtGui import QColor, QPalette, QPixmap  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication, QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QLabel, QListWidget, QMainWindow,
    QMessageBox, QPushButton, QRadioButton, QStackedWidget, QVBoxLayout, QWidget,
)

TRY_SECONDS = 20
SCHEMES = Path('/usr/share/color-schemes')


def scheme_palette(name: str) -> QPalette | None:
    cfg = configparser.ConfigParser(interpolation=None)
    if not cfg.read(SCHEMES / f'{name}.colors'):
        return None

    def color(section, key):
        try:
            r, g, b = (int(x) for x in cfg[section][key].split(',')[:3])
            return QColor(r, g, b)
        except (KeyError, ValueError):
            return None
    pal = QPalette()
    for role, section, key in [(QPalette.Window, 'Colors:Window', 'BackgroundNormal'),
                               (QPalette.WindowText, 'Colors:Window', 'ForegroundNormal'),
                               (QPalette.Base, 'Colors:View', 'BackgroundNormal'),
                               (QPalette.Text, 'Colors:View', 'ForegroundNormal'),
                               (QPalette.Button, 'Colors:Button', 'BackgroundNormal'),
                               (QPalette.ButtonText, 'Colors:Button', 'ForegroundNormal'),
                               (QPalette.Highlight, 'Colors:Selection', 'BackgroundNormal'),
                               (QPalette.HighlightedText, 'Colors:Selection', 'ForegroundNormal')]:
        c = color(section, key)
        if c is not None:
            pal.setColor(role, c)
    return pal


def theme_sample(name: str) -> QWidget:
    """A real Qt window rendered with the scheme's actual colours."""
    box = QFrame(); box.setAutoFillBackground(True); box.setFrameShape(QFrame.StyledPanel)
    pal = scheme_palette(name)
    if pal:
        box.setPalette(pal)
    lay = QVBoxLayout(box)
    title = QLabel('Documents'); title.setStyleSheet('font-size: 18px; font-weight: 600;')
    lay.addWidget(title)
    files = QListWidget(); files.addItems(['Project notes.odt', 'Holiday photos', 'Budget 2027.ods', 'Ideas.md'])
    files.setCurrentRow(1); lay.addWidget(files)
    row = QHBoxLayout(); row.addWidget(QCheckBox('Show hidden files')); row.addStretch()
    row.addWidget(QPushButton('Open')); lay.addLayout(row)
    if pal:
        for w in box.findChildren(QWidget):
            w.setPalette(pal)
    box.setMinimumHeight(300)
    return box


class Appearance(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('OREZ Appearance'); self.resize(1000, 640)
        self.state = model.load_state()
        self.pending = None  # (group, choice, revert commands)
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick); self.remaining = 0

        root = QWidget(); outer = QHBoxLayout(root); self.setCentralWidget(root)
        self.groups = QListWidget(); self.groups.setFixedWidth(200)
        for key, (title, _) in model.GROUPS.items():
            self.groups.addItem(title)
        outer.addWidget(self.groups)

        right = QVBoxLayout(); outer.addLayout(right, 1)
        self.choices_row = QHBoxLayout(); right.addLayout(self.choices_row)
        self.summary = QLabel(); self.summary.setWordWrap(True); right.addWidget(self.summary)
        self.preview = QStackedWidget(); self.preview.setMinimumHeight(360); right.addWidget(self.preview, 1)
        self.note = QLabel(); self.note.setWordWrap(True); self.note.setStyleSheet('color: palette(mid);')
        right.addWidget(self.note)
        buttons = QHBoxLayout(); buttons.addStretch()
        self.try_btn = QPushButton('Try it for 20 seconds'); self.try_btn.clicked.connect(self.try_choice)
        self.keep_btn = QPushButton('Keep'); self.keep_btn.clicked.connect(self.keep); self.keep_btn.setEnabled(False)
        self.undo_btn = QPushButton('Put it back'); self.undo_btn.clicked.connect(self.revert); self.undo_btn.setEnabled(False)
        for b in (self.try_btn, self.keep_btn, self.undo_btn):
            buttons.addWidget(b)
        right.addLayout(buttons)

        self.radio = QButtonGroup(self); self.radio.buttonClicked.connect(lambda b: self.show_choice(b.property('choice')))
        self.groups.currentRowChanged.connect(self.show_group); self.groups.setCurrentRow(0)

    def current_group(self) -> str:
        return list(model.GROUPS)[self.groups.currentRow()]

    def show_group(self, _row):
        if self.pending:
            self.revert()
        while self.choices_row.count():
            w = self.choices_row.takeAt(0).widget()
            if w:
                self.radio.removeButton(w); w.deleteLater()
        group = self.current_group(); chosen = self.state.get(group)
        for i, opt in enumerate(model.GROUPS[group][1]):
            rb = QRadioButton(opt.title); rb.setProperty('choice', opt.id)
            self.radio.addButton(rb); self.choices_row.addWidget(rb)
            if opt.id == chosen or (chosen is None and i == 0):
                rb.setChecked(True)
        self.choices_row.addStretch()
        self.show_choice(self.radio.checkedButton().property('choice'))

    def show_choice(self, choice):
        group = self.current_group()
        opt = next(o for o in model.GROUPS[group][1] if o.id == choice)
        self.summary.setText(f'<b>{opt.title}</b> — {opt.summary}')
        while self.preview.count():
            w = self.preview.widget(0); self.preview.removeWidget(w); w.deleteLater()
        image = model.preview_image(group, choice)
        if group == 'theme':
            self.preview.addWidget(theme_sample(choice))
            self.note.setText('Preview drawn with the real colour scheme. Try it to see your whole desktop.')
        elif image:
            label = QLabel(); label.setAlignment(Qt.AlignCenter)
            label.setPixmap(QPixmap(str(image)).scaled(720, 405, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.preview.addWidget(label)
            self.note.setText('Real image.' if group == 'wallpaper' else 'Screenshot captured from an actual OREZ boot.')
        else:
            label = QLabel('Press “Try it” to see this on your real desktop.\nNothing is kept unless you press Keep.')
            label.setAlignment(Qt.AlignCenter); self.preview.addWidget(label); self.note.setText('')

    def try_choice(self):
        if self.pending:
            self.revert()
        group = self.current_group(); choice = self.radio.checkedButton().property('choice')
        revert = model.snapshot(group)
        errors = model.run(model.plan(group, choice))
        if errors:
            model.run(revert)
            QMessageBox.warning(self, 'Could not apply', '\n'.join(errors)); return
        self.pending = (group, choice, revert); self.remaining = TRY_SECONDS
        self.keep_btn.setEnabled(True); self.undo_btn.setEnabled(True); self.try_btn.setEnabled(False)
        self.tick(); self.timer.start(1000)

    def tick(self):
        if not self.pending:
            return
        self.note.setText(f'Trying it now. Going back automatically in {self.remaining} s unless you press Keep.')
        if self.remaining <= 0:
            self.revert(); return
        self.remaining -= 1

    def keep(self):
        if not self.pending:
            return
        group, choice, _ = self.pending
        model.save_choice(group, choice); self.state[group] = choice
        self.finish('Kept. You can change it again any time.')

    def revert(self):
        if not self.pending:
            return
        errors = model.run(self.pending[2])
        self.finish('Put back as it was.' if not errors else 'Some settings could not be restored: ' + '; '.join(errors))

    def finish(self, message):
        self.timer.stop(); self.pending = None
        self.keep_btn.setEnabled(False); self.undo_btn.setEnabled(False); self.try_btn.setEnabled(True)
        self.note.setText(message)

    def closeEvent(self, event):
        if self.pending:
            self.revert()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv); app.setApplicationName('OREZ Appearance')
    w = Appearance(); w.show(); return app.exec()


if __name__ == '__main__':
    sys.exit(main())
