"""Actual Qt Calendar/Reuz interaction, local data, exports and timer lifecycle."""
import json
import os
from pathlib import Path
import sys
from PySide6.QtCore import Qt,QDate,QTimer
from PySide6.QtGui import QColor,QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog
sys.path.insert(0,'/usr/lib/orez')
from daily_models import Calendar,ClockSettings
from daily_ui import CalendarWindow,TimeWindow

assert os.getuid()!=0 and Path('/.dockerenv').exists()
OUT=Path(os.environ.get('OREZ_DAILY_EVIDENCE','/evidence/daily-apps'));OUT.mkdir(exist_ok=False)
QApplication.setAttribute(Qt.AA_DontUseNativeDialogs)
app=QApplication([]);app.setQuitOnLastWindowClosed(False)
calendar=CalendarWindow();calendar.show();QTest.qWait(200)
results=[];counter=0;window=calendar


def shot(name,widget=None):
    global counter
    counter+=1;app.processEvents()
    assert (widget or window).grab().save(str(OUT/f'{counter:02d}-{name}.png'))


def click(widget):QTest.mouseClick(widget,Qt.LeftButton);app.processEvents()


def scenario(name,function):
    try:detail=function();record={'name':name,'status':'passed','detail':detail}
    except Exception as error:record={'name':name,'status':'failed','error':repr(error)}
    results.append(record);shot(name);print(json.dumps(record),flush=True)


def modal(action,name,answer):
    errors=[]
    def reply():
        dialog=app.activeModalWidget()
        try:
            assert isinstance(dialog,QMessageBox)
            shot(name,dialog);click(dialog.button(answer))
        except Exception as error:
            errors.append(repr(error))
            if dialog:dialog.reject()
    QTimer.singleShot(100,reply);action();assert not errors,errors


def save_edit():
    calendar.month.setSelectedDate(QDate(2026,11,5))
    calendar.title.setFocus();QTest.keyClicks(calendar.title,'OREZ planning')
    calendar.notes.setPlainText('Local notes: 日本語, privacy; no cloud account.')
    click(calendar.save)
    assert len(calendar.calendar.events('2026-11-05'))==1
    shot('calendar-saved')
    item=calendar.events.item(0)
    QTest.mouseClick(calendar.events.viewport(),Qt.LeftButton,pos=calendar.events.visualItemRect(item).center())
    calendar.title.setFocus();QTest.keyClick(calendar.title,Qt.Key_A,Qt.ControlModifier);QTest.keyClicks(calendar.title,'Release review')
    click(calendar.save)
    assert calendar.calendar.events('2026-11-05')[0][2]=='Release review'
    return 'Actual event creation and editing persisted to local SQLite.'


def export():
    errors=[];target=OUT/'calendar.ics'
    def choose():
        dialog=app.activeModalWidget()
        try:
            assert isinstance(dialog,QFileDialog)
            dialog.selectFile(str(target));shot('calendar-export-dialog',dialog);dialog.accept()
        except Exception as error:
            errors.append(repr(error))
            if dialog:dialog.reject()
    QTimer.singleShot(150,choose);click(calendar.export)
    assert not errors,errors
    assert 'SUMMARY:Release review' in target.read_text() and '日本語' in target.read_text()
    assert target.stat().st_mode&0o777==0o600
    return 'Actual save dialog exported .ics with UTF-8 notes and private permissions.'


def delete():
    item=calendar.events.item(0);calendar.events.setCurrentItem(item)
    modal(lambda:click(calendar.remove),'calendar-cancel-delete',QMessageBox.Cancel)
    assert len(calendar.calendar.events('2026-11-05'))==1
    modal(lambda:click(calendar.remove),'calendar-confirm-delete',QMessageBox.Yes)
    assert calendar.calendar.events('2026-11-05')==[]
    return 'Cancel preserves the event; explicit delete removes only that event.'


def reuz():
    global window
    calendar.close();window=TimeWindow();window.show();QTest.qWait(200)
    window.zone.setCurrentText('Asia/Kolkata');window.hours24.setChecked(False);click(window.apply)
    persisted=ClockSettings()
    assert persisted.timezone=='Asia/Kolkata' and persisted.format=='12h'
    assert 'Asia/Kolkata' in window.date.text()
    return 'Timezone and format preferences saved; system clock not changed.'


def timer():
    window.tabs.setCurrentIndex(1);window.minutes.setValue(0);window.seconds.setValue(2)
    click(window.timer_start);QTest.qWait(300);click(window.timer_pause)
    paused=window.countdown.remaining();QTest.qWait(200)
    assert abs(window.countdown.remaining()-paused)<.01;shot('reuz-paused-timer')
    click(window.timer_pause);QTest.qWait(2100)
    assert window.timer_status.text()=='Timer finished.' and window.countdown.finished
    return 'Real Qt countdown pause/resume/completion; no physical audio or wake test.'


def stopwatch():
    window.tabs.setCurrentIndex(2);click(window.watch_start);QTest.qWait(350)
    click(window.watch_lap);click(window.watch_start)
    assert window.stopwatch.laps[0]>=.2 and window.laps.count()==1
    elapsed=window.stopwatch.elapsed();QTest.qWait(200)
    assert abs(window.stopwatch.elapsed()-elapsed)<.01
    shot('reuz-stopwatch-lap');click(window.watch_reset)
    assert window.stopwatch.elapsed()==0 and window.laps.count()==0
    return 'Default buttons start/pause, lap and reset the real stopwatch.'


def themes():
    import configparser
    for name in ['OREZInk','OREZPaper']:
        config=configparser.ConfigParser();config.read('/usr/share/color-schemes/'+name+'.colors')
        palette=QPalette()
        for role,section,key in [(QPalette.Window,'Window','BackgroundNormal'),(QPalette.WindowText,'Window','ForegroundNormal'),
                                 (QPalette.Base,'View','BackgroundNormal'),(QPalette.Text,'View','ForegroundNormal'),
                                 (QPalette.Button,'Button','BackgroundNormal'),(QPalette.ButtonText,'Button','ForegroundNormal'),
                                 (QPalette.Highlight,'Selection','BackgroundNormal'),(QPalette.HighlightedText,'Selection','ForegroundNormal')]:
            palette.setColor(role,QColor(*map(int,config['Colors:'+section][key].split(','))))
        app.setPalette(palette);QTest.qWait(100);shot('reuz-'+name)
        pixel=window.grab().toImage().pixelColor(5,5)
        assert pixel==palette.color(QPalette.Window),(name,pixel.name(),palette.color(QPalette.Window).name())
    return 'Real app renders both packaged palette definitions; this is app-level color testing, not a full Plasma-session theme switch.'


def close_cancel():
    click(window.watch_start)
    modal(window.close,'reuz-close-cancel',QMessageBox.Cancel);assert window.isVisible()
    modal(window.close,'reuz-close-confirm',QMessageBox.Yes);assert not window.isVisible() and not window.tick.isActive()
    assert app.primaryScreen().grabWindow(0).save(str(OUT/'closed-app-display.png'))
    return 'Active-work warning is cancellable; confirmed close stops UI timers and leaves no background app.'


for name,fn in [('calendar-create-edit',save_edit),('calendar-ics-export',export),('calendar-delete-consent',delete),
                ('reuz-preferences',reuz),('reuz-countdown',timer),('reuz-stopwatch',stopwatch),('native-theme-palettes',themes),('close-active-clock',close_cancel)]:scenario(name,fn)
(OUT/'results.json').write_text(json.dumps({'scope':'Native Qt apps in disposable Xvfb container, not ISO/hardware acceptance',
 'scenarios':results,'uid':os.getuid(),'remote_requests':False,'background_alarm_service':False},indent=2)+'\n')
sys.exit(any(r['status']!='passed' for r in results))
