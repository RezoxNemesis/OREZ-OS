#!/usr/bin/env python3
"""Exercise actual KWin windows and restart Plasma in the disposable fixture.

Window-management checks use KWin's public scripting interface. The launcher
capture uses actual pointer input into the nested X11 display. Neither is an
ISO boot or a hardware test. Every scenario retains its actual final frame.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

assert os.getuid() != 0 and Path('/.dockerenv').exists()
evidence = Path('/evidence')
results = []
serial = 0


def command(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, timeout=20).strip()


def script(body):
    global serial
    serial += 1
    name = f'orez-scenario-{serial}'
    marker = f'OREZ_NATIVE_{serial}:'
    path = evidence / f'{name}.js'
    path.write_text(f'try {{ var result = (function() {{ {body} }})(); print("{marker}" + JSON.stringify({{value:result}})); }} catch(e) {{ print("{marker}" + JSON.stringify({{error:String(e)}})); }}')
    identifier = command('qdbus6', 'org.kde.KWin', '/Scripting', 'org.kde.kwin.Scripting.loadScript', str(path), name)
    assert identifier.isdigit(), identifier
    command('qdbus6', 'org.kde.KWin', f'/Scripting/Script{identifier}', 'org.kde.kwin.Script.run')
    for _ in range(50):
        for line in (evidence / 'kwin.log').read_text(errors='replace').splitlines():
            if marker in line:
                data = json.loads(line.split(marker, 1)[1])
                command('qdbus6', 'org.kde.KWin', '/Scripting', 'org.kde.kwin.Scripting.unloadScript', name)
                assert 'error' not in data, data
                return data['value']
        time.sleep(.1)
    raise AssertionError(f'Missing KWin response {marker}')


def capture(name):
    subprocess.run(['scrot', str(evidence / f'{name}.png')], env={**os.environ, 'DISPLAY': ':99'}, check=True, timeout=10)


def scenario(name, action):
    try:
        detail = action()
        results.append({'name': name, 'status': 'passed', 'detail': detail})
        print(f'PASS {name}: {json.dumps(detail)}', flush=True)
    except Exception as error:
        results.append({'name': name, 'status': 'failed', 'error': str(error)})
        print(f'FAIL {name}: {error}', flush=True)
    finally:
        capture(name)


def windows():
    data = script('return workspace.windowList().map(w => ({app:String(w.resourceClass), caption:w.caption, width:w.frameGeometry.width, height:w.frameGeometry.height}));')
    for app in ['systemsettings', 'dolphin', 'konsole']:
        assert any(app in w['app'].lower() and w['width'] > 100 and w['height'] > 100 for w in data), (app, data)
    return data


def launcher():
    # Real pointer input. Existence of a popup is inspected visually, not
    # inferred from xdotool's exit code; mark this result accordingly.
    command('xdotool', 'mousemove', '30', '870', 'click', '1')
    time.sleep(2)
    capture('03-launcher-open')
    command('xdotool', 'key', 'Escape')
    return {'input_delivered': True, 'popup_verdict': 'requires visual review of 03-launcher-open.png'}


def window_management():
    assert script("var w=workspace.windowList().find(w=>String(w.resourceClass).includes('dolphin')); w.minimized=true; return w.minimized;") is True
    time.sleep(.3)
    capture('04-window-minimized')
    state = script("var w=workspace.windowList().find(w=>String(w.resourceClass).includes('dolphin')); w.minimized=false; workspace.activeWindow=w; w.frameGeometry={x:60,y:70,width:760,height:600}; return {minimized:w.minimized,active:workspace.activeWindow===w};")
    assert state == {'minimized': False, 'active': True}, state
    time.sleep(1)
    geometry = script("var w=workspace.windowList().find(w=>String(w.resourceClass).includes('dolphin')); return {width:w.frameGeometry.width,height:w.frameGeometry.height};")
    assert geometry['width'] == 760 and geometry['height'] == 600, geometry
    return {**state, **geometry, 'interface': 'KWin scripting API'}


def workspaces():
    data = script("workspace.createDesktop(workspace.desktops.length,'OREZ QA'); workspace.currentDesktop=workspace.desktops[workspace.desktops.length-1]; return {count:workspace.desktops.length,current:workspace.currentDesktop.name};")
    assert data['count'] >= 2 and data['current'] == 'OREZ QA', data
    time.sleep(1)
    capture('05-second-workspace')
    script('workspace.currentDesktop=workspace.desktops[0]; workspace.removeDesktop(workspace.desktops[workspace.desktops.length-1]); return workspace.desktops.length;')
    return data


def plasma_state():
    value = command('qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', 'var d=desktops()[0]; d.currentConfigGroup=["Wallpaper","org.kde.image","General"]; print(JSON.stringify({desktops:desktops().length,panels:panels().length,wallpaper:d.readConfig("Image")}));')
    with (evidence / 'plasma-state-responses.txt').open('a') as log:
        log.write(value + '\n')
    return json.loads(value)


def restart():
    before = plasma_state()
    assert before['desktops'] > 0 and before['panels'] > 0 and 'orez' in before['wallpaper'].lower(), before
    os.kill(int(sys.argv[1]), signal.SIGTERM)
    for _ in range(50):
        if not Path(f'/proc/{sys.argv[1]}').exists():
            break
        time.sleep(.1)
    log = (evidence / 'plasma-restart.log').open('w')
    process = subprocess.Popen(['plasmashell', '--no-respawn'], stdout=log, stderr=subprocess.STDOUT)
    for _ in range(40):
        assert process.poll() is None, 'Plasma restart exited'
        try:
            after = plasma_state()
            if after == before:
                break
        except (subprocess.SubprocessError, ValueError):
            pass
        time.sleep(.5)
    else:
        raise AssertionError('Desktop/panel/wallpaper state did not recover')
    time.sleep(2)
    return {'before': before, 'after': after, 'app_windows_after_restart': windows()}


scenario('02-native-window-assertions', windows)
scenario('03-launcher-input', launcher)
scenario('04-minimize-resize-restore', window_management)
scenario('05-workspace-switch', workspaces)
scenario('06-plasma-restart', restart)
(evidence / 'desktop-results.json').write_text(json.dumps(results, indent=2) + '\n')
sys.exit(any(result['status'] != 'passed' for result in results))
