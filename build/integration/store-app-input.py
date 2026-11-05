"""Real native app input checks, isolated test account, no custom key mapping.

Screenshots show actual Xvfb windows, not an ISO desktop or Android runtime.
Keep sandbox failures visible; never add --no-sandbox to force a browser pass.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

assert os.getuid() != 0 and Path('/.dockerenv').exists()
OUT = Path(os.environ.get('OREZ_APP_INPUT_EVIDENCE', '/evidence/store-app-input'))
OUT.mkdir(exist_ok=True)
children = []
results = []


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, timeout=20).strip()


def shot(name):
    run('scrot', str(OUT / (name + '.png')))


def launch(name, args):
    with (OUT / (name + '.log')).open('w') as log:
        child = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
    children.append(child)
    return child


def vlc():
    video = OUT / 'keyboard-mouse-test.mp4'
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=640x360:rate=25', '-t', '60', '-c:v', 'libx264',
        '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-y', str(video))
    child = launch('vlc', ['vlc', '--no-one-instance', '--no-metadata-network-access',
        '--no-qt-privacy-ask', '--avcodec-hw=none', '--vout=xcb_x11', str(video)])
    for _ in range(40):
        services = [s.strip() for s in run('qdbus6').splitlines()
                    if s.strip().startswith('org.mpris.MediaPlayer2.vlc')]
        if services:
            break
        assert child.poll() is None, 'VLC exited'
        time.sleep(.25)
    assert services, 'No VLC media service'
    base = ['qdbus6', services[0], '/org/mpris/MediaPlayer2']
    def prop(name):
        return run(*base, 'org.mpris.MediaPlayer2.Player.' + name)
    time.sleep(2)
    assert prop('PlaybackStatus') == 'Playing'
    windows = run('xdotool', 'search', '--onlyvisible', '--pid', str(child.pid)).splitlines()
    window = next(w for w in windows if 'VLC media player' in run('xdotool', 'getwindowname', w))
    run('xdotool', 'windowfocus', '--sync', window)
    shot('01-vlc-actual-playback')
    before = int(prop('Position')); time.sleep(1); after = int(prop('Position'))
    assert after > before + 500000, (before, after)
    # Deliver default physical-style key input; MPRIS is read-only observation.
    run('xdotool', 'key', '--clearmodifiers', 'space'); time.sleep(.4)
    assert prop('PlaybackStatus') == 'Paused', 'Default Space did not pause VLC'
    paused = int(prop('Position')); time.sleep(.7)
    assert abs(int(prop('Position')) - paused) < 200000
    shot('02-vlc-default-space-paused')
    run('xdotool', 'key', '--clearmodifiers', 'space'); time.sleep(.4)
    assert prop('PlaybackStatus') == 'Playing', 'Default Space did not resume VLC'
    raw = run('xdotool', 'getwindowgeometry', '--shell', window)
    geometry = dict(line.split('=', 1) for line in raw.splitlines())
    x = int(geometry['X']) + int(geometry['WIDTH']) // 2
    y = int(geometry['Y']) + int(geometry['HEIGHT']) // 2
    run('xdotool', 'mousemove', str(x), str(y), 'click', '3'); time.sleep(.3)
    shot('03-vlc-mouse-context-menu')
    # The visually reviewed first popup item is Pause. Verify the resulting
    # playback state, not an assumed Qt class name in X11's window title.
    tree = run('xwininfo', '-root', '-tree')
    (OUT / 'vlc-context-window-tree.txt').write_text(tree + '\n')
    run('xdotool', 'mousemove', str(x + 40), str(y + 13), 'click', '1')
    time.sleep(.4)
    assert prop('PlaybackStatus') == 'Paused', 'Mouse menu Pause did not pause VLC'
    shot('04-vlc-mouse-paused')
    run('xdotool', 'windowfocus', '--sync', window)
    run('xdotool', 'key', '--clearmodifiers', 'space'); time.sleep(.3)
    assert prop('PlaybackStatus') == 'Playing'
    run('xdotool', 'key', '--clearmodifiers', 'f'); time.sleep(.3)
    assert run(*base, 'org.mpris.MediaPlayer2.Fullscreen') == 'true'
    shot('04-vlc-default-f-fullscreen')
    run('xdotool', 'key', '--clearmodifiers', 'f'); time.sleep(.3)
    assert run(*base, 'org.mpris.MediaPlayer2.Fullscreen') == 'false'
    run('xdotool', 'key', '--clearmodifiers', 'ctrl+q'); child.wait(timeout=10)
    shot('05-vlc-default-quit')
    return {'version': run('dpkg-query', '-W', '-f=${Version}', 'vlc'),
            'positions_us': [before, after], 'space_pause_resume': True,
            'mouse_context_menu': True, 'fullscreen_f': True, 'quit_ctrl_q': True,
            'custom_key_mapping': False, 'hardware_acceleration_tested': False,
            'audio_tested': False, 'scope': 'generated local video, native Linux application'}


def brave():
    # Native official binary, temporary QA profile, no app wrapper or sandbox bypass.
    child = launch('brave', ['/usr/bin/brave-browser', '--no-first-run',
        '--no-default-browser-check', '--user-data-dir=' + str(OUT / 'brave-profile'), 'about:blank'])
    time.sleep(3)
    shot('06-brave-start-attempt')
    if child.poll() is not None:
        error = (OUT / 'brave.log').read_text()
        return {'status': 'blocked', 'exit_code': child.returncode,
                'reason': error[-2500:], 'sandbox_bypassed': False,
                'scope': 'Native launch attempted; no working browser or browsing claim'}
    windows = run('xdotool', 'search', '--onlyvisible', '--class', 'brave-browser').splitlines()
    assert windows, 'No visible Brave window'
    run('xdotool', 'windowfocus', '--sync', windows[-1])
    run('xdotool', 'key', 'ctrl+l')
    run('xdotool', 'type', '--clearmodifiers', 'brave://version')
    run('xdotool', 'key', 'Return'); time.sleep(1)
    shot('07-brave-native-version')
    return {'status': 'opened', 'keyboard_navigation': 'delivered; screenshot requires review',
            'sandbox_bypassed': False, 'network_tested': False, 'full_functionality_tested': False}


try:
    for name, function in [('vlc-default-keyboard-mouse', vlc), ('native-brave', brave)]:
        if os.environ.get('OREZ_APP_INPUT_FILTER') not in [None, name]:
            continue
        try:
            detail = function()
            record = {'name': name, 'status': detail.pop('status', 'passed'), 'detail': detail}
        except Exception as error:
            record = {'name': name, 'status': 'failed', 'error': str(error)}
        results.append(record); print(json.dumps(record), flush=True)
        shot(name + '-result')
finally:
    for child in children:
        if child.poll() is None:
            child.terminate()
    (OUT / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
sys.exit(any(r['status'] == 'failed' for r in results))
