"""Native app component checks against packages installed in the actual ISO base.

Run as an ordinary UID in the offline staging chroot. Qt offscreen images are
real widget renders, not a Plasma desktop, login, physical-input or GPU test.
The OREZ Python sources/palettes are copied into /run only for this fixture.
"""
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from PySide6.QtCore import QDate,QEventLoop,QTimer
from PySide6.QtGui import QColor,QPalette
from PySide6.QtWidgets import QApplication

FIXTURE=Path(__file__).resolve().parent
assert FIXTURE.parent==Path('/run') and FIXTURE.name.startswith('orez-app-check.')
assert os.getuid()==1500 and os.environ.get('QT_QPA_PLATFORM')=='offscreen'
assert Path.home()==FIXTURE/'home'
sys.path.insert(0,str(FIXTURE/'source'))
from daily_models import Calendar,ClockSettings
from daily_ui import CalendarWindow,TimeWindow

OUT=FIXTURE/'evidence';results=[]
app=QApplication([]);app.setQuitOnLastWindowClosed(False)


def wait(ms):
    loop=QEventLoop();QTimer.singleShot(ms,loop.quit);loop.exec()


def shot(name,window):
    app.processEvents();assert window.grab().save(str(OUT/(name+'.png')))


def palette(name):
    config=configparser.ConfigParser();config.read(FIXTURE/'palettes'/(name+'.colors'))
    value=QPalette()
    for role,section,key in [(QPalette.Window,'Window','BackgroundNormal'),(QPalette.WindowText,'Window','ForegroundNormal'),
                            (QPalette.Base,'View','BackgroundNormal'),(QPalette.Text,'View','ForegroundNormal'),
                            (QPalette.Button,'Button','BackgroundNormal'),(QPalette.ButtonText,'Button','ForegroundNormal'),
                            (QPalette.Highlight,'Selection','BackgroundNormal'),(QPalette.HighlightedText,'Selection','ForegroundNormal')]:
        value.setColor(role,QColor(*map(int,config['Colors:'+section][key].split(','))))
    app.setPalette(value);wait(50)


def record(name,detail):
    results.append({'name':name,'status':'passed','detail':detail});print(json.dumps(results[-1]),flush=True)


try:
    versions={}
    # Brave's shell wrapper uses /dev/fd process substitution, unavailable here.
    # Check the actual executable explicitly, without pretending the wrapper or
    # sandboxed browser session was qualified by a version command.
    for name,command,pattern in [('Brave',['/opt/brave.com/brave/brave','--version'],r'^Brave Browser [0-9].*$'),
                                 ('VLC',['/usr/bin/vlc','--version'],r'^VLC version [0-9].*$'),
                                 ('SuperTux',['/usr/games/supertux2','--version'],r'^supertux2 v[0-9].*$')]:
        # The documented data-path variable avoids relying on /proc/self/exe
        # discovery in this intentionally minimal chroot. Not an installed-OS
        # default or proof of normal-path launch in a complete desktop session.
        env={**os.environ,'SUPERTUX2_DATA_DIR':'/usr/share/games/supertux2'}
        result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30,env=env)
        (OUT/(name.lower()+'-version.txt')).write_text(result.stdout)
        assert result.returncode==0,(name,result.returncode,result.stdout[-500:])
        matched=re.findall(pattern,result.stdout,re.MULTILINE)
        assert len(matched)==1,(name,'Expected version record missing',result.stdout)
        versions[name]=matched[0]
    record('native-binary-startup',{'versions':versions,'supertux_explicit_data_path':True,'brave_shell_wrapper_tested':False,'gui_playback_browsing_or_gameplay_tested':False})
    palette('OREZPaper');window=CalendarWindow();window.show();wait(200)
    window.month.setSelectedDate(QDate(2026,11,6));window.title.setText('First PC release review')
    window.notes.setPlainText('Local calendar • native Qt\nBoot, login and installer qualification still pending.')
    shot('01-calendar-editor',window);window.save.click();wait(100)
    assert window.calendar.events('2026-11-06')[0][2]=='First PC release review'
    shot('02-calendar-saved',window);window.close()
    again=Calendar();assert len(again.events('2026-11-06'))==1;again.close()
    record('calendar-save-reopen','Real SQLite persistence and button signal on installed Qt; no simulated storage.')
    window=TimeWindow();window.show();window.zone.setCurrentText('Asia/Kolkata');window.hours24.setChecked(False)
    window.apply.click();wait(100);assert ClockSettings().timezone=='Asia/Kolkata'
    shot('03-reuz-clock-paper',window);palette('OREZInk');shot('04-reuz-clock-ink',window)
    assert window.grab().toImage().pixelColor(5,5)==app.palette().color(QPalette.Window)
    record('clock-preferences-palettes','Native clock, saved display timezone, Paper and Ink app palettes; no system-time change.')
    window.tabs.setCurrentIndex(1);window.minutes.setValue(0);window.seconds.setValue(1)
    window.timer_start.click();wait(200);window.timer_pause.click();remaining=window.countdown.remaining()
    wait(200);assert abs(remaining-window.countdown.remaining())<.01
    shot('05-reuz-paused',window);window.timer_pause.click();wait(1100)
    assert window.countdown.finished and window.timer_status.text()=='Timer finished.'
    shot('06-reuz-finished',window);window.close();assert not window.tick.isActive()
    record('countdown-pause-finish-close','Real Qt event loop, pause/resume and completion; confirmed timer shutdown after close.')
finally:
    (OUT/'results.json').write_text(json.dumps({'scope':'Actual base chroot, native Qt OFFSCREEN components; not a desktop/ISO boot',
        'uid':os.getuid(),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (FIXTURE/'source').glob('*.py')},
        'scenarios':results,'physical_input_tested':False,'app_sandbox_enforcement_tested':False,
        'installation_approved':False},indent=2)+'\n')
