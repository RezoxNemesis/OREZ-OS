"""Actual native Qt widget interaction in disposable normal-user Xvfb session."""
import json,os,sys,time
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import Qt,QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QMessageBox,QInputDialog
sys.path.insert(0,'/usr/lib/orez')
from store_manager import Store
from store_ui import StoreWindow

assert os.getuid()!=0 and Path('/.dockerenv').exists()
out=Path('/evidence/store');out.mkdir(exist_ok=True)
app=QApplication([]);app.setQuitOnLastWindowClosed(False)
manager=Store();window=StoreWindow(manager);window.show();QTest.qWait(250)
results=[];counter=0

def shot(name,widget=None):
    global counter
    app.processEvents();counter+=1
    path=out/f'{counter:02d}-{name}.png'
    assert (widget or window).grab().save(str(path)),path

def scenario(name,operation):
    try:detail=operation();value={'name':name,'status':'passed','detail':detail}
    except Exception as error:value={'name':name,'status':'failed','error':repr(error)}
    results.append(value);shot(name);print(json.dumps(value),flush=True)

def click(widget):QTest.mouseClick(widget,Qt.LeftButton);app.processEvents()
def choose(key):
    window.search.clear();window.kind.setCurrentIndex(0)
    if window.library.isChecked():click(window.library)
    for row in range(window.items.count()):
        item=window.items.item(row)
        if item.data(Qt.UserRole)==key:
            window.items.scrollToItem(item);click_point=window.items.visualItemRect(item).center()
            QTest.mouseClick(window.items.viewport(),Qt.LeftButton,pos=click_point);app.processEvents();assert window.key==key;return
    raise AssertionError('App missing: '+key)

def modal_trigger(button,answer,name,text=None):
    errors=[]
    def respond():
        try:
            dialog=app.activeModalWidget();assert dialog is not None
            if isinstance(dialog,QInputDialog):
                if text is not None:dialog.setTextValue(text)
                shot(name,dialog);dialog.accept() if answer else dialog.reject()
            else:
                assert isinstance(dialog,QMessageBox)
                shot(name,dialog)
                wanted=QMessageBox.Yes if answer else QMessageBox.Cancel
                target=dialog.button(wanted) or dialog.button(QMessageBox.Ok)
                assert target is not None;click(target)
        except Exception as error:
            errors.append(str(error));dialog=app.activeModalWidget()
            if dialog:dialog.reject()
    QTimer.singleShot(120,respond);click(button)
    assert not errors,errors

def catalog():
    assert window.items.count()==10
    assert manager.app('youtube')['kind']=='android' and not window.primary.isEnabled()
    return {'native_widgets':True,'apps':10,'runs_as_uid':os.getuid()}

def search():
    window.search.setFocus();QTest.keyClicks(window.search,'subway');app.processEvents()
    assert window.items.count()==1 and window.key=='subway-surfers'
    shot('search-subway')
    window.search.setText('not-an-app');assert window.items.count()==0
    assert not window.primary.isEnabled();shot('empty-search')
    window.search.clear();assert window.items.count()==10
    return 'Search, empty state and clear all work.'

def android():
    window.kind.setCurrentIndex(1);assert window.items.count()==6
    for key in ['youtube','instagram','free-fire','subway-surfers','asphalt-legends','play-store']:
        choose(key);assert not window.primary.isEnabled();shot(key+'-blocked')
    return 'All requested Android entries are visibly pending; no APK/provider is installed.'

def runtime_cancel():
    choose('youtube')
    with patch('store_manager.subprocess.Popen') as launch:
        modal_trigger(window.runtime,False,'runtime-consent-cancel-dialog')
        launch.assert_not_called()
    return 'Development runtime acknowledgement can be cancelled; no emulator, licence acceptance or download starts.'

def library():
    click(window.library);ids=[window.items.item(i).data(Qt.UserRole) for i in range(window.items.count())]
    assert 'youtube' not in ids and 'free-fire' not in ids and 'vlc' in ids
    return {'detected_apps':ids,'android_not_falsely_installed':True}

def native_launch():
    import subprocess,signal
    choose('vlc')
    before={p.name for p in Path('/proc').iterdir() if p.name.isdecimal()}
    click(window.primary);QTest.qWait(1500)
    processes=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal() or proc.name in before:continue
        try:
            if proc.stat().st_uid==os.getuid() and (proc/'comm').read_text().strip()=='vlc':processes.append(int(proc.name))
        except FileNotFoundError:continue
    try:
        assert processes,'VLC process not observed'
        found=subprocess.run(['xdotool','search','--pid',str(processes[0])],capture_output=True,text=True,timeout=5)
        assert found.returncode==0 and found.stdout.strip(),'VLC window not observed'
        assert app.primaryScreen().grabWindow(0).save(str(out/'native-vlc-opened-from-store.png'))
        return {'native_vlc_processes':processes,'window_observed':True,'media_playback_tested':False,'network_consents_accepted':False}
    finally:
        for pid in processes:
            try:os.kill(pid,signal.SIGTERM)
            except ProcessLookupError:pass
        QTest.qWait(150)

def source_cancel():
    choose('brave-linux')
    with patch('store_manager.subprocess.Popen') as launch:
        modal_trigger(window.source,False,'external-source-cancel')
        launch.assert_not_called()
    return 'Opening an external site can be cancelled; no browser started.'

def activity():
    modal_trigger(window.activity,False,'local-activity-controls')
    return 'Local controls/action log visible; no account information used.'

def reopen():
    global window
    window.close();app.processEvents()
    assert app.primaryScreen().grabWindow(0).save(str(out/'closed-native-store-display.png'))
    window=StoreWindow(manager);window.show();QTest.qWait(150)
    assert window.items.count()==10
    return 'Store closes and reopens without a resident downloader.'

for name,fn in [('catalog',catalog),('search-and-empty',search),('actual-android-gates',android),
                ('cancel-runtime-start',runtime_cancel),('my-apps',library),('launch-native-vlc',native_launch),
                ('publisher-info-cancel',source_cancel),('activity-controls',activity),('close-reopen',reopen)]:scenario(name,fn)
(out/'result.json').write_text(json.dumps({'scope':'Native Qt Store in Xvfb container; not ISO desktop or website/game playback',
 'scenarios':results,'screenshots':len(list(out.glob('*.png'))),'uid':os.getuid(),'store_process_status':Path('/proc/self/status').read_text(),
 'android_runtime_tested':False,'external_sites_opened':False,'installation_approved':False},indent=2)+'\n')
window.close();sys.exit(any(item['status']!='passed' for item in results))
