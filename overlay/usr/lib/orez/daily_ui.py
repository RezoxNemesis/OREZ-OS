"""Native OREZ Calendar and Reuz Time desktop windows; local storage only."""
import argparse
import math
import os
from pathlib import Path
import sqlite3
import stat
import sys
from zoneinfo import available_timezones
from PySide6.QtCore import Qt,QDate,QTimer
from PySide6.QtWidgets import (QApplication,QCalendarWidget,QCheckBox,QComboBox,
    QFileDialog,QHBoxLayout,QLabel,QLineEdit,QListWidget,QListWidgetItem,QMainWindow,
    QMessageBox,QPlainTextEdit,QPushButton,QSpinBox,QTabWidget,QVBoxLayout,QWidget)
from daily_models import Calendar,ClockSettings,Countdown,Stopwatch,duration

STYLE='''QWidget{background:palette(window);color:palette(window-text);font-family:"Noto Sans";font-size:14px}
QLineEdit,QPlainTextEdit,QListWidget,QComboBox,QSpinBox{background:palette(base);color:palette(text);border:1px solid palette(mid);border-radius:6px;padding:8px}
QPushButton{background:palette(button);color:palette(button-text);border:1px solid palette(mid);border-radius:7px;padding:10px 16px}
QPushButton:hover{background:palette(midlight)} QPushButton:focus{border:2px solid palette(highlight)}
QLabel#headline{font-size:32px} QLabel#digits{font-size:52px;font-weight:300}
QTabWidget::pane{border:1px solid palette(mid);border-radius:8px} QTabBar::tab{padding:12px 24px}
QTabBar::tab:selected{background:palette(highlight);color:palette(highlighted-text)}'''


def button(text, callback, layout):
    value=QPushButton(text);value.clicked.connect(callback);layout.addWidget(value);return value


class LocalWindow(QMainWindow):
    def refresh_palette(self,palette):
        # Qt caches palette() values in a widget stylesheet. Re-polish when the
        # desktop changes its application palette, including while we are open.
        self.setStyleSheet('');self.setPalette(palette);self.setStyleSheet(STYLE)
    def structure(self,title,subtitle):
        self.setWindowTitle(title);self.resize(940,700);self.setMinimumSize(720,560)
        QApplication.instance().paletteChanged.connect(self.refresh_palette)
        self.setStyleSheet(STYLE);root=QWidget();self.setCentralWidget(root)
        layout=QVBoxLayout(root);layout.setContentsMargins(28,24,28,24);layout.setSpacing(14)
        heading=QLabel(title);heading.setObjectName('headline');layout.addWidget(heading)
        note=QLabel(subtitle);note.setWordWrap(True);layout.addWidget(note)
        return layout
    def operation(self, callback):
        try:return callback()
        except (OSError,ValueError,sqlite3.Error) as error:
            QMessageBox.warning(self,'OREZ',str(error))


class CalendarWindow(LocalWindow):
    def __init__(self, calendar=None):
        super().__init__();self.calendar=calendar or Calendar();self.event_id=None
        layout=self.structure('OREZ Calendar','Your days, kept locally. All-day events and notes; no account, synchronization or background reminders.')
        row=QHBoxLayout();layout.addLayout(row,1)
        left=QVBoxLayout();row.addLayout(left,1);self.month=QCalendarWidget();self.month.setGridVisible(False);self.month.setAccessibleName('Calendar date');left.addWidget(self.month)
        self.events=QListWidget();self.events.setAccessibleName('Events on selected day');left.addWidget(self.events,1)
        right=QVBoxLayout();row.addLayout(right,1)
        self.date=QLabel();right.addWidget(self.date)
        right.addWidget(QLabel('Event title'));self.title=QLineEdit();self.title.setMaxLength(160);self.title.setAccessibleName('Event title');right.addWidget(self.title)
        right.addWidget(QLabel('Notes'));self.notes=QPlainTextEdit();self.notes.setAccessibleName('Event notes');right.addWidget(self.notes,1)
        controls=QHBoxLayout();right.addLayout(controls)
        self.new=button('New',self.clear_editor,controls);self.save=button('Save event',lambda:self.operation(self.save_event),controls)
        self.remove=button('Delete',self.delete_event,controls)
        lower=QHBoxLayout();layout.addLayout(lower)
        self.export=button('Export calendar (.ics)',lambda:self.operation(self.export_calendar),lower)
        self.info=button('Data and controls',self.data_info,lower)
        self.status=QLabel('Saved only on this computer. Export a copy for backup.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.month.selectionChanged.connect(self.refresh);self.events.currentItemChanged.connect(self.select)
        self.refresh()
    def day(self):return self.month.selectedDate().toString(Qt.ISODate)
    def clear_editor(self):
        self.event_id=None;self.title.clear();self.notes.clear();self.remove.setEnabled(False);self.events.clearSelection();self.title.setFocus()
    def refresh(self):
        self.date.setText(self.month.selectedDate().toString('dddd, d MMMM yyyy'))
        self.events.clear()
        for event in self.calendar.events(self.day()):
            item=QListWidgetItem(event[2]);item.setData(Qt.UserRole,event);self.events.addItem(item)
        self.clear_editor()
    def select(self,item,*unused):
        if not item:return
        event=item.data(Qt.UserRole);self.event_id=event[0];self.title.setText(event[2]);self.notes.setPlainText(event[3]);self.remove.setEnabled(True)
    def save_event(self):
        self.calendar.save(self.day(),self.title.text(),self.notes.toPlainText(),self.event_id)
        self.refresh();self.status.setText('Event saved locally.')
    def delete_event(self):
        if self.event_id is None:return
        if QMessageBox.question(self,'Delete event?','Delete this local event? Export a backup first if you need to retain it.',QMessageBox.Yes|QMessageBox.Cancel,QMessageBox.Cancel)==QMessageBox.Yes:
            event_id=self.event_id
            def remove():
                self.calendar.delete(event_id);self.refresh();self.status.setText('Event deleted locally.')
            self.operation(remove)
    def export_calendar(self):
        target,_=QFileDialog.getSaveFileName(self,'Export calendar',str(Path.home()/'OREZ-calendar.ics'),'Calendar (*.ics)')
        if not target:return
        data=self.calendar.export_ics()
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('Choose a regular calendar file, not a device.')
            stream.truncate(0);stream.write(data);stream.flush();os.fsync(stream.fileno())
        self.status.setText('Calendar exported to '+target)
    def data_info(self):
        QMessageBox.information(self,'Calendar data and controls',
            'Local database: '+str(self.calendar.root/'events.sqlite3')+'\n\nNo account, network access or background service. Events are all-day only. Export .ics for backup; no import or reminders are implemented yet. Closing the app stops it. Other programs running as your user can access your files; this is not encrypted storage.')
    def closeEvent(self,event):self.calendar.close();event.accept()


class TimeWindow(LocalWindow):
    def __init__(self, settings=None):
        super().__init__();self.settings=settings or ClockSettings();self.stopwatch=Stopwatch();self.countdown=Countdown()
        layout=self.structure('Reuz Time','OREZ desktop edition • local clock, countdown and stopwatch')
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1)
        clock=QWidget();clock_layout=QVBoxLayout(clock);clock_layout.setContentsMargins(24,24,24,24);self.tabs.addTab(clock,'Clock')
        self.clock=QLabel();self.clock.setObjectName('digits');self.clock.setAlignment(Qt.AlignCenter);clock_layout.addWidget(self.clock)
        self.date=QLabel();self.date.setAlignment(Qt.AlignCenter);clock_layout.addWidget(self.date)
        clock_layout.addStretch();clock_layout.addWidget(QLabel('Display timezone (does not change the system clock)'))
        self.zone=QComboBox();self.zone.setEditable(True);self.zone.setInsertPolicy(QComboBox.NoInsert);self.zone.addItems(sorted(available_timezones()));self.zone.setCurrentText(self.settings.timezone);self.zone.setAccessibleName('Display timezone');clock_layout.addWidget(self.zone)
        self.hours24=QCheckBox('Use 24-hour time');self.hours24.setChecked(self.settings.format=='24h');clock_layout.addWidget(self.hours24)
        self.apply=button('Save clock preferences',lambda:self.operation(self.save_settings),clock_layout)
        timer=QWidget();timer_layout=QVBoxLayout(timer);timer_layout.setContentsMargins(24,24,24,24);self.tabs.addTab(timer,'Timer')
        self.remaining=QLabel();self.remaining.setObjectName('digits');self.remaining.setAlignment(Qt.AlignCenter);timer_layout.addWidget(self.remaining)
        inputs=QHBoxLayout();timer_layout.addLayout(inputs)
        self.minutes=QSpinBox();self.minutes.setRange(0,1439);self.minutes.setValue(5);self.minutes.setSuffix(' min');self.minutes.setAccessibleName('Timer minutes');inputs.addWidget(self.minutes)
        self.seconds=QSpinBox();self.seconds.setRange(0,59);self.seconds.setSuffix(' sec');self.seconds.setAccessibleName('Timer seconds');inputs.addWidget(self.seconds)
        buttons=QHBoxLayout();timer_layout.addLayout(buttons)
        self.timer_start=button('Start / restart',lambda:self.operation(self.start_timer),buttons)
        self.timer_pause=button('Pause / resume',lambda:self.operation(self.pause_timer),buttons)
        self.timer_reset=button('Reset',self.reset_timer,buttons)
        self.timer_status=QLabel('Timer alerts only while Reuz is open. It does not wake a sleeping PC.');self.timer_status.setWordWrap(True);timer_layout.addWidget(self.timer_status);timer_layout.addStretch()
        watch=QWidget();watch_layout=QVBoxLayout(watch);watch_layout.setContentsMargins(24,24,24,24);self.tabs.addTab(watch,'Stopwatch')
        self.elapsed=QLabel();self.elapsed.setObjectName('digits');self.elapsed.setAlignment(Qt.AlignCenter);watch_layout.addWidget(self.elapsed)
        buttons=QHBoxLayout();watch_layout.addLayout(buttons)
        self.watch_start=button('Start / pause',self.toggle_stopwatch,buttons)
        self.watch_lap=button('Lap',self.add_lap,buttons);self.watch_reset=button('Reset',self.reset_stopwatch,buttons)
        self.laps=QListWidget();self.laps.setAccessibleName('Stopwatch laps');watch_layout.addWidget(self.laps)
        button('Data and controls',self.data_info,layout)
        self.tick=QTimer(self);self.tick.timeout.connect(self.update_clock);self.tick.start(1000);self.update_clock()
    def save_settings(self):
        self.settings.save(self.zone.currentText().strip(),'24h' if self.hours24.isChecked() else '12h');self.update_clock()
    def start_timer(self):
        self.countdown.start(self.minutes.value()*60+self.seconds.value());self.timer_status.setText('Timer running. Keep Reuz open.');self.update_clock()
    def pause_timer(self):
        if self.countdown.deadline is None:self.countdown.start();self.timer_status.setText('Timer resumed.')
        else:self.countdown.pause();self.timer_status.setText('Timer paused.')
        self.update_clock()
    def reset_timer(self):self.countdown.reset();self.timer_status.setText('Timer reset.');self.update_clock()
    def toggle_stopwatch(self):
        if self.stopwatch.started is None:self.stopwatch.start()
        else:self.stopwatch.pause()
        self.update_clock()
    def add_lap(self):self.laps.addItem(f'{len(self.stopwatch.laps)+1:02d}    '+duration(self.stopwatch.lap()))
    def reset_stopwatch(self):self.stopwatch.reset();self.laps.clear();self.update_clock()
    def update_clock(self):
        clock,date=self.settings.display();self.clock.setText(clock);self.date.setText(date+' · '+self.settings.timezone)
        self.elapsed.setText(duration(self.stopwatch.elapsed()));self.remaining.setText(duration(math.ceil(self.countdown.remaining())))
        if self.countdown.check_finished():
            self.timer_status.setText('Timer finished.');QApplication.beep();self.show();self.raise_()
        interval=100 if self.stopwatch.started is not None or self.countdown.deadline is not None else 1000
        if self.tick.interval()!=interval:self.tick.setInterval(interval)
    def data_info(self):
        QMessageBox.information(self,'Reuz data and controls','Preferences: '+str(self.settings.path)+'\n\nThis native desktop edition uses Reuz timezone/format defaults. No web/MCP server, microphone or Android service is included. Clock settings do not change system time. Timers and stopwatch count elapsed sleep time but cannot wake the PC. Closing stops them; no background service, account sync or scheduled alarms. Preferences persist; timer/lap state does not. Reset controls are visible in each tab.')
    def closeEvent(self,event):
        if self.countdown.deadline is not None or self.stopwatch.started is not None:
            if QMessageBox.question(self,'Close Reuz?','Closing stops the active timer/stopwatch. No background alarm will remain.',QMessageBox.Yes|QMessageBox.Cancel,QMessageBox.Cancel)!=QMessageBox.Yes:
                event.ignore();return
        self.tick.stop();event.accept()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('application',choices=['calendar','time']);args=parser.parse_args()
    app=QApplication(sys.argv)
    try:window=CalendarWindow() if args.application=='calendar' else TimeWindow()
    except (OSError,ValueError,sqlite3.Error) as error:
        QMessageBox.critical(None,'OREZ application',str(error));return 1
    window.show();return app.exec()


if __name__=='__main__':sys.exit(main())
