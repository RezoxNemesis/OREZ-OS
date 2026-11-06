"""Practical OREZ component tour in an isolated native Plasma session.

Screenshots are real nested-desktop frames. No ISO boot, hardware, installer,
internet, frame-rate or six-GiB certification is implied by these checks.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

assert os.getuid()==1500 and Path('/.dockerenv').exists()
E=Path('/evidence');results=[];children=[];serial=0
outer={**os.environ,'DISPLAY':':99'}
sockets=[p for p in Path('/tmp/.X11-unix').glob('X*') if p.name!='X99']
assert len(sockets)==1,'Expected one private Xwayland display'
env={**os.environ,'QT_QPA_PLATFORM':'xcb','DISPLAY':':'+sockets[0].name[1:]}
auth=list(Path(os.environ['XDG_RUNTIME_DIR']).glob('xauth*'))+list(Path('/tmp').glob('xauth*'))
auth=[p for p in auth if p.is_file() and not p.is_symlink() and p.stat().st_uid==os.getuid()]
# KWin may use the already-owned local display without a separate cookie file.
# Probe the existing session; never change xhost, permissions or authentication.
for candidate in [*auth,None]:
    env.pop('XAUTHORITY',None)
    if candidate:env['XAUTHORITY']=str(candidate)
    probe=subprocess.run(['xdpyinfo'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    if probe.returncode==0:break
else:raise AssertionError('Cannot access the existing private Xwayland session')
fixture=Path.home()/('OREZ-Tour-'+str(os.getpid()))
fixture.mkdir(mode=0o700);source=fixture/'Documents';target=fixture/'Archive'
source.mkdir();target.mkdir();(source/'tour-note.txt').write_text('OREZ tour fixture. No personal files.\n日本語\n')


def run(*args,environment=None):
    return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT,timeout=25,env=environment).strip()


def shot(name):
    run('scrot',str(E/(name+'.png')),environment=outer)


def keys(*args):
    if args[0]=='key':args=('key','--clearmodifiers',*args[1:])
    run('xdotool',*args,environment=outer)


def file_menu(label):
    # Actual native context menu, visually inspected in qa10-13. Qt omits its
    # SHOWING state from AT-SPI in this nested fixture; use the known pinned
    # 1440x900 layout and C.UTF-8 locale. Subsequent filesystem checks verify
    # the operation rather than assuming a successful click is a pass.
    positions={'Rename…':417,'Move to Trash':452}
    keys('mousemove','330','220','click','3');time.sleep(.4)
    shot('menu-'+('rename' if label=='Rename…' else 'trash'))
    keys('mousemove','405',str(positions[label]),'click','1')


def kwin(body):
    global serial
    serial+=1;name='orez-tour-'+str(serial);marker='OREZ_TOUR_'+str(serial)+':'
    path=E/(name+'.js')
    path.write_text('try {var v=(function(){'+body+'})();print('+json.dumps(marker)+'+JSON.stringify({value:v}));}catch(e){print('+json.dumps(marker)+'+JSON.stringify({error:String(e)}));}')
    identifier=run('qdbus6','org.kde.KWin','/Scripting','org.kde.kwin.Scripting.loadScript',str(path),name)
    assert identifier.isdigit(),identifier
    run('qdbus6','org.kde.KWin','/Scripting/Script'+identifier,'org.kde.kwin.Script.run')
    try:
        for _ in range(60):
            for line in (E/'kwin.log').read_text(errors='replace').splitlines():
                if marker in line:
                    value=json.loads(line.split(marker,1)[1]);assert 'error' not in value,value
                    return value['value']
            time.sleep(.1)
        raise AssertionError('No KWin response')
    finally:run('qdbus6','org.kde.KWin','/Scripting','org.kde.kwin.Scripting.unloadScript',name)


def launch(name,args):
    with (E/(name+'.log')).open('w') as stream:
        child=subprocess.Popen(args,stdout=stream,stderr=subprocess.STDOUT,env=env)
    children.append(child)
    return child


def window(child):
    for _ in range(50):
        assert child.poll() is None,'Application exited; inspect its log'
        query=subprocess.run(['xdotool','search','--onlyvisible','--pid',str(child.pid)],env=env,capture_output=True,text=True)
        if query.returncode==0 and query.stdout.strip():
            values=query.stdout.splitlines()
            return max(values,key=lambda value:int(run('xdotool','getwindowgeometry','--shell',value,environment=env).split('WIDTH=')[1].splitlines()[0]))
        time.sleep(.2)
    raise AssertionError('Visible window missing')


def focus(child):
    value=window(child);run('xdotool','windowactivate','--sync',value,environment=env);time.sleep(.2)
    return value


def wait_file(path,present=True):
    for _ in range(35):
        if path.exists()==present:return
        time.sleep(.1)
    raise AssertionError('File operation did not reach expected state: '+str(path))


def scenario(name,fn):
    try:record={'name':name,'status':'passed','detail':fn()}
    except Exception as error:record={'name':name,'status':'failed','error':repr(error)}
    results.append(record);shot(name);print(json.dumps(record),flush=True)


def appearance():
    state=run('qdbus6','org.kde.plasmashell','/PlasmaShell','org.kde.PlasmaShell.evaluateScript',
              'var d=desktops()[0];d.currentConfigGroup=["Wallpaper","org.kde.image","General"];print(d.readConfig("Image"));')
    assert 'OREZ-Rest' in state,state;shot('01-desktop-current-default')
    for palette in ['OREZInk','OREZPaper']:
        run('plasma-apply-colorscheme',palette);time.sleep(1)
        assert run('kreadconfig6','--file','kdeglobals','--group','General','--key','ColorScheme')==palette
        shot('02-desktop-'+palette)
    run('plasma-apply-wallpaperimage','/usr/share/wallpapers/OREZ-Horizon/contents/images/1280x720.jpg');time.sleep(1)
    shot('03-desktop-horizon');run('plasma-apply-wallpaperimage','/usr/share/wallpapers/OREZ-Rest/contents/images/1280x720.jpg');time.sleep(1)
    return {'wallpaper':state,'palettes_applied':['OREZInk','OREZPaper'],'final_demo_palette':'OREZPaper','default_first_boot_palette_not_changed_in_source':True}


def launcher():
    keys('mousemove','30','870','click','1');time.sleep(1);shot('04-launcher-open')
    keys('type','--clearmodifiers','OREZ');time.sleep(1);shot('05-launcher-orez-search')
    keys('key','Escape')
    return {'input_delivered':True,'visual_review_required':True,'scope':'Native launcher search, not an application download'}


def files():
    global dolphin
    dolphin=launch('dolphin',['dolphin','--new-window',str(source)]);focus(dolphin)
    kwin("var w=workspace.windowList().find(w=>String(w.resourceClass).includes('dolphin'));w.frameGeometry={x:100,y:80,width:1100,height:700};return w.caption;")
    time.sleep(1);shot('06-dolphin-files')
    keys('key','Home','ctrl+c','ctrl+l');keys('type','--clearmodifiers',str(target));keys('key','Return');time.sleep(.5);keys('key','ctrl+v')
    copied=target/'tour-note.txt';wait_file(copied)
    assert copied.read_bytes()==(source/'tour-note.txt').read_bytes();shot('07-file-copy')
    focus(dolphin);file_menu('Rename…');time.sleep(.6)
    shot('08-rename-dialog');keys('key','ctrl+a');keys('type','--clearmodifiers','renamed-note.txt');keys('key','Return')
    renamed=target/'renamed-note.txt';wait_file(renamed);assert not copied.exists();shot('08-file-rename')
    file_menu('Move to Trash');wait_file(renamed,False);shot('09-file-to-trash')
    keys('key','ctrl+z');wait_file(renamed);assert renamed.read_bytes()==(source/'tour-note.txt').read_bytes();shot('10-file-undo')
    keys('key','ctrl+t');time.sleep(.4)
    keys('mousemove','1090','139','click','1');time.sleep(.5);shot('11-dolphin-tabs-split')
    return {'copy_rename_trash_undo':True,'original_unchanged':True,'tabs_split_input_delivered':True,'fixture':str(fixture),'physical_usb_tested':False}


def multitasking():
    global terminal
    terminal=launch('konsole',['konsole','--separate','-e','bash','-c',
        'printf "OREZ local tour — standard user\\n\\n"; id; printf "\\nAI status\\n"; orezctl ai; printf "\\nNative terminal and multitasking\\n"; python3 --version; read -r -t 150'])
    focus(terminal)
    value=kwin("var ds=workspace.windowList().filter(w=>['dolphin','konsole'].some(a=>String(w.resourceClass).includes(a)));ds.forEach((w,i)=>{w.minimized=false;w.frameGeometry={x:i?735:15,y:80,width:690,height:700};});return ds.map(w=>({app:String(w.resourceClass),width:w.frameGeometry.width}));")
    assert len(value)==2,value;time.sleep(.5);shot('12-files-and-terminal')
    assert kwin("var w=workspace.windowList().find(w=>String(w.resourceClass).includes('dolphin'));w.minimized=true;return w.minimized;") is True
    shot('13-minimized-files');kwin("var w=workspace.windowList().find(w=>String(w.resourceClass).includes('dolphin'));w.minimized=false;return w.minimized;")
    state=kwin("workspace.createDesktop(workspace.desktops.length,'OREZ Tour');workspace.currentDesktop=workspace.desktops[workspace.desktops.length-1];return {count:workspace.desktops.length,name:workspace.currentDesktop.name};")
    assert state['count']>=2 and state['name']=='OREZ Tour';time.sleep(.4);shot('14-second-workspace')
    kwin('workspace.currentDesktop=workspace.desktops[0];workspace.removeDesktop(workspace.desktops[workspace.desktops.length-1]);return workspace.desktops.length;')
    return {'windows':value,'minimize_restore':True,'workspace':state,'interface':'Real KWin scripting interface'}


def restart():
    # A controlled shell restart; this is not a kernel crash or recovery test.
    before=kwin("return workspace.windowList().filter(w=>['dolphin','konsole'].some(a=>String(w.resourceClass).includes(a))).map(w=>String(w.resourceClass)).sort();")
    assert len(before)==2,before
    os.kill(int(sys.argv[1]),signal.SIGTERM);time.sleep(1)
    with (E/'plasma-tour-restart.log').open('w') as stream:
        shell=subprocess.Popen(['plasmashell','--no-respawn'],stdout=stream,stderr=subprocess.STDOUT)
    children.append(shell)
    for _ in range(40):
        assert shell.poll() is None,'Replacement shell exited'
        try:
            count=run('qdbus6','org.kde.plasmashell','/PlasmaShell','org.kde.PlasmaShell.evaluateScript','print(panels().length)')
            if count.isdigit() and int(count)>0:break
        except subprocess.SubprocessError:pass
        time.sleep(.3)
    else:raise AssertionError('Panel did not return')
    after=kwin("return workspace.windowList().filter(w=>['dolphin','konsole'].some(a=>String(w.resourceClass).includes(a))).map(w=>String(w.resourceClass)).sort();")
    assert before==after and dolphin.poll() is None and terminal.poll() is None
    time.sleep(1);shot('15-panel-restart-apps-preserved')
    return {'apps_before':before,'apps_after':after,'panel_returned':True,'kernel_driver_power_failure_tested':False}


try:
    for name,fn in [('appearance',appearance),('launcher',launcher),('file-operations',files),('multitasking',multitasking),('shell-restart',restart)]:scenario(name,fn)
finally:
    for child in children:
        if child.poll() is None:child.terminate()
    (E/'tour-results.json').write_text(json.dumps({'scope':'Native nested Plasma container; not a booted ISO',
        'scenarios':results,'uid':os.getuid(),'hardware_tested':False,'installation_approved':False},indent=2)+'\n')
sys.exit(any(row['status']=='failed' for row in results))
