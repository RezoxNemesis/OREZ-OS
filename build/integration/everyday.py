"""Real native desktop activities; preserve failures and environmental blocks."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

assert os.getuid() != 0 and Path('/.dockerenv').exists()
E = Path('/evidence')
results = []
children = []


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, timeout=30, **kwargs).strip()


def launch(name, args, env=None):
    log = (E / (name + '.log')).open('w')
    process = subprocess.Popen(args, env=env, stdout=log, stderr=subprocess.STDOUT)
    children.append(process)
    return process


def shot(name):
    subprocess.run(['scrot', str(E / (name + '.png'))], env={**os.environ, 'DISPLAY': ':99'}, check=True, timeout=10)


def scenario(name, function):
    selected = os.environ.get('OREZ_EVERYDAY_FILTER', '').split(',')
    if selected != [''] and name not in selected:
        return
    before = time.monotonic()
    try:
        detail = function()
        record = {'name': name, 'status': 'passed', 'detail': detail}
    except Exception as error:
        record = {'name': name, 'status': 'failed', 'error': str(error)}
        if isinstance(error, subprocess.CalledProcessError): record['output'] = error.output
    record['seconds'] = round(time.monotonic() - before, 2)
    results.append(record); print(json.dumps(record), flush=True)
    shot(name)


def plasma_state():
    return run('qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', 'var d=desktops()[0];d.currentConfigGroup=["Wallpaper","org.kde.image","General"];print(d.readConfig("Image"));')


def wallpaper():
    before = plasma_state(); assert 'OREZ-Rest' in before, before
    shot('01-owner-default-wallpaper')
    run('plasma-apply-wallpaperimage', '/usr/share/wallpapers/OREZ-Horizon/contents/images/1280x720.jpg')
    time.sleep(2); after = plasma_state(); assert 'OREZ-Horizon' in after, after
    shot('02-owner-alternative-wallpaper')
    run('plasma-apply-wallpaperimage', '/usr/share/wallpapers/OREZ-Rest/contents/images/1280x720.jpg')
    return {'default': before, 'alternative': after, 'restored': plasma_state()}


def settings():
    app = launch('settings', ['systemsettings', 'kcm_colors'])
    time.sleep(3)
    before = run('kreadconfig6', '--file', 'kdeglobals', '--group', 'General', '--key', 'ColorScheme') or 'BreezeLight'
    run('plasma-apply-colorscheme', 'BreezeDark'); time.sleep(2)
    after = run('kreadconfig6', '--file', 'kdeglobals', '--group', 'General', '--key', 'ColorScheme')
    assert after == 'BreezeDark', after
    shot('03-settings-dark-applied')
    run('plasma-apply-colorscheme', before); time.sleep(2)
    restored = run('kreadconfig6', '--file', 'kdeglobals', '--group', 'General', '--key', 'ColorScheme') or 'BreezeLight'
    assert restored == before, restored
    shot('04-settings-restored')
    app.terminate()
    return {'before': before, 'applied': after, 'restored': restored, 'method': 'native KDE apply tool + effective KConfig, actual Settings window'}


def android_controls():
    state = json.loads(run('orez-android', 'status'))
    assert not state['autostart'] and not state['kvm_available'] and not state['installed']
    app = launch('android-manager', ['orez-android', 'gui'])
    time.sleep(2); shot('05-android-manager-controls')
    process = subprocess.run(['orez-android', 'start'], text=True, capture_output=True)
    assert process.returncode == 2 and 'KVM' in process.stderr, process.stderr
    (E / 'android-status.json').write_text(json.dumps(state, indent=2))
    app.terminate()
    # Close only this test's kdialog, if its parent is still processing SIGTERM.
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if proc.stat().st_uid == os.getuid() and proc.joinpath('comm').read_text().strip() == 'kdialog':
                os.kill(int(proc.name), 15)
        except OSError: pass
    return {'manager_controls': 'visible', 'start': 'correctly rejected unavailable KVM', 'play_store_download': 'BLOCKED: no installed Android guest, KVM or Google sign-in; SDK is development-only'}


def xwayland_environment():
    # The compositor publishes DISPLAY/XAUTHORITY in its D-Bus activation env.
    # Start a tiny child through KWin so it receives those real session values.
    script = Path('/tmp/orez-session-env.sh')
    script.write_text('#!/bin/sh\nprintf "%s\\n%s\\n" "$DISPLAY" "$XAUTHORITY" > /evidence/xwayland-environment.txt\n')
    script.chmod(0o755)
    # Wayland KDE apps already work; find KWin's private Xauthority for X clients.
    candidates = list(Path(os.environ['XDG_RUNTIME_DIR']).glob('xauth*')) + list(Path('/tmp').glob('xauth*'))
    sockets = [p for p in Path('/tmp/.X11-unix').glob('X*') if p.name != 'X99']
    env = {**os.environ, 'QT_QPA_PLATFORM':'xcb', 'SDL_VIDEODRIVER':'x11'}
    if sockets:
        env['DISPLAY'] = ':' + sockets[0].name[1:]
        if candidates: env['XAUTHORITY'] = str(candidates[0])
    else:
        # Recorded fallback: native X11 applications on the same private Xvfb
        # framebuffer, outside the nested KWin window. Never call this Wayland.
        env['DISPLAY'] = ':99'
    (E / 'native-x11-environment.json').write_text(json.dumps({k:env.get(k) for k in ['DISPLAY','XAUTHORITY','QT_QPA_PLATFORM']}, indent=2))
    return env


def vlc_playback():
    video = E / 'moving-test.mp4'
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=25',
        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '45', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-y', str(video))
    run('pulseaudio', '--start', '--exit-idle-time=-1', '--log-target=file:/evidence/pulse.log')
    run('pactl', 'load-module', 'module-null-sink', 'sink_name=orez_test')
    run('pactl', 'set-default-sink', 'orez_test')
    app = launch('vlc', ['vlc', '--no-one-instance', '--no-metadata-network-access', '--no-qt-privacy-ask', '--avcodec-hw=none', '--aout=pulse', '--vout=xcb_x11', str(video)], env=xwayland_environment())
    for _ in range(40):
        services = [s for s in run('qdbus6').splitlines() if s.strip().startswith('org.mpris.MediaPlayer2.vlc')]
        if services: break
        assert app.poll() is None, 'VLC exited; inspect vlc.log'
        time.sleep(.25)
    assert services, 'VLC MPRIS service unavailable'
    service = services[0].strip(); base = ['qdbus6', service, '/org/mpris/MediaPlayer2']
    def prop(name): return run(*base, 'org.mpris.MediaPlayer2.Player.' + name)
    time.sleep(3); assert prop('PlaybackStatus') == 'Playing'
    first = int(prop('Position')); shot('06-vlc-playing')
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'pulse', '-i', 'orez_test.monitor', '-t', '2', '-ac', '1', '-ar', '44100', '-y', '/evidence/vlc-audio.wav')
    second = int(prop('Position')); assert second > first + 1000000, (first,second)
    import wave, array
    with wave.open('/evidence/vlc-audio.wav') as wav: samples = array.array('h', wav.readframes(wav.getnframes()))
    assert samples and max(abs(v) for v in samples) > 100, 'No decoded audio samples at virtual sink'
    run(*base, 'org.mpris.MediaPlayer2.Player.Pause'); time.sleep(.3)
    paused = int(prop('Position')); time.sleep(1); held = int(prop('Position'))
    assert prop('PlaybackStatus') == 'Paused' and abs(held-paused) < 200000, (paused,held)
    shot('07-vlc-paused')
    run(*base, 'org.mpris.MediaPlayer2.Player.Seek', '10000000'); time.sleep(.5)
    sought = int(prop('Position')); assert sought > paused + 8000000, (paused,sought)
    run(*base, 'org.mpris.MediaPlayer2.Player.Play'); time.sleep(2); shot('08-vlc-resumed-after-seek')
    run(*base, 'org.mpris.MediaPlayer2.Quit')
    return {'playing_positions_us':[first,second], 'paused_positions_us':[paused,held], 'seek_position_us':sought,
            'audio_peak':max(abs(v) for v in samples), 'audio_output':'virtual sink only; no physical speaker test'}


def game():
    env = xwayland_environment()
    binary = shutil.which('supertux2') or '/usr/games/supertux2'
    files = run('dpkg-query', '-L', 'supertux-data').splitlines()
    (E / 'supertux-data-files.txt').write_text('\n'.join(files))
    levels = [Path(p) for p in files if p.endswith('.stl')]
    assert levels, 'No packaged starting level found'
    level = next((p for p in levels if p.name == 'welcome_antarctica.stl'), None)
    assert level is not None, 'Expected packaged playable level missing; do not substitute an intro'
    app = launch('supertux', [binary, '--window', '--geometry', '960x640', '--show-pos', '--show-fps', str(level)], env=env)
    time.sleep(7); assert app.poll() is None, 'SuperTux exited'
    # Use actual key input, not a simulated screenshot or fabricated score.
    ids = run('xdotool', 'search', '--onlyvisible', '--name', 'SuperTux', env=env).splitlines()
    assert ids, 'SuperTux window missing'
    window = ids[-1]
    run('xdotool', 'windowactivate', '--sync', window, env=env)
    shot('09-supertux-introduction')
    input_env = {**os.environ, 'DISPLAY': ':99'}
    run('xdotool', 'mousemove', '700', '400', 'click', '1', env=input_env)
    run('xdotool', 'keydown', 'space', env=input_env); time.sleep(.4)
    run('xdotool', 'keyup', 'space', env=input_env)
    time.sleep(3)
    shot('10-supertux-active-level-before-input')
    # A live process or successful XTEST request is not gameplay proof. Reject
    # the predominantly black introduction for this pinned, snowy outdoor level.
    from PIL import Image
    raw = run('xdotool', 'getwindowgeometry', '--shell', window, env=env)
    geometry = {k:int(v) for k,v in (line.split('=',1) for line in raw.splitlines())}
    pixels = Image.open(E/'10-supertux-active-level-before-input.png').convert('RGB').crop(
        (geometry['X'], geometry['Y'], geometry['X']+geometry['WIDTH'], geometry['Y']+geometry['HEIGHT']))
    visible = sum(max(pixel)>60 for pixel in pixels.getdata()) / (pixels.width*pixels.height)
    assert visible > .4, f'Playable scene not established; bright-pixel fraction {visible:.3f}'
    run('xdotool', 'keydown', 'Right', env=input_env); time.sleep(2)
    run('xdotool', 'keydown', 'space', env=input_env); time.sleep(.3)
    run('xdotool', 'keyup', 'space', env=input_env)
    run('xdotool', 'keyup', 'Right', env=input_env)
    time.sleep(2); shot('12-supertux-after-input')
    app.terminate()
    return {'application':'SuperTux native Linux game', 'level':str(level), 'input':'Right and jump delivered', 'gameplay':'requires visual review of position overlay/captures; no Android/AAA/FPS certification'}


def resource_state():
    state={'scope':'visible cgroup, potentially shared parent; not proof of a container limit',
           'process_cgroup':Path('/proc/self/cgroup').read_text().strip()}
    for name in ['memory.max','memory.current','memory.peak','memory.events','cpu.max','cpu.stat']:
        path=Path('/sys/fs/cgroup')/name
        if path.exists(): state[name]=path.read_text().strip()
    return state


def desktop_latency():
    measurements=[]
    for _ in range(12):
        start=time.monotonic(); value=plasma_state(); measurements.append(round((time.monotonic()-start)*1000,2))
        assert 'OREZ-Rest' in value
    peak=sorted(measurements)[-1]
    assert peak<1000, f'Native desktop control response exceeded one second: {measurements}'
    return {'dbus_round_trip_ms':measurements,'max_ms':peak,'scope':'component API responsiveness, not input-to-photon latency or target-PC FPS'}


try:
    (E / 'resources-before.json').write_text(json.dumps(resource_state(),indent=2))
    pressure=int(os.environ.get('OREZ_PRESSURE_MB','0'))
    assert 0<=pressure<=2048
    if pressure:
        hog=launch('memory-pressure',['python3','-c',f'import time;data=bytearray({pressure}*1024*1024);print("allocated",len(data),flush=True);time.sleep(180)'])
        for _ in range(40):
            assert hog.poll() is None, 'Memory pressure helper exited'
            if 'allocated' in (E/'memory-pressure.log').read_text(): break
            time.sleep(.25)
        else: raise AssertionError('Memory pressure fixture did not become ready')
    scenario('owner-wallpaper-selection', wallpaper)
    scenario('native-settings-apply-restore', settings)
    scenario('android-controls-and-kvm-denial', android_controls)
    scenario('vlc-playback-audio-pause-seek', vlc_playback)
    scenario('native-game-input', game)
    scenario('desktop-responsiveness-under-load', desktop_latency)
    selected = os.environ.get('OREZ_EVERYDAY_FILTER', '').split(',')
    if selected == [''] or 'brave-scenarios' in selected:
        browser = subprocess.run(['node', '/input/everyday-browser.mjs'], text=True, capture_output=True, timeout=150)
        (E / 'browser-driver.log').write_text(browser.stdout + browser.stderr)
        if (E / 'browser-results.json').exists(): results.extend(json.loads((E / 'browser-results.json').read_text()))
        else: results.append({'name':'brave-scenarios','status':'failed','error':browser.stderr[-1500:]})
finally:
    (E / 'resources-after.json').write_text(json.dumps(resource_state(),indent=2))
    for child in children:
        if child.poll() is None: child.terminate()
    (E / 'everyday-results.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2), flush=True)
raise SystemExit(any(r['status']=='failed' for r in results))
