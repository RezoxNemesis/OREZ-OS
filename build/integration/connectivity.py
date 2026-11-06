"""Native Settings controls in a private offline desktop. Never saves credentials."""
from collections import deque
import json
import os
from pathlib import Path
import subprocess
import time
import pyatspi

assert os.getuid() != 0 and Path('/.dockerenv').exists()
E = Path('/evidence')
results, children = [], []


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, timeout=20, **kwargs).strip()


def shot(name):
    subprocess.run(['scrot', str(E / (name + '.png'))], env={**os.environ, 'DISPLAY': ':99'}, check=True, timeout=10)


def desktop_input(*args):
    # KWin global shortcuts require input to the outer nested display.
    return run('xdotool', *args, env={**os.environ, 'DISPLAY': ':99'})


def nodes():
    queue = deque((app, 0) for app in pyatspi.Registry.getDesktop(0) if app.name == 'systemsettings')
    seen = set()
    while queue and len(seen) < 900:
        node, depth = queue.popleft()
        if hash(node) in seen or depth > 24:
            continue
        seen.add(hash(node))
        # Qt exposes cached children of hidden sidebar/configuration windows.
        # Their individual SHOWING flags are insufficient for targeting input.
        if node.getRoleName() == 'frame' and not node.getState().contains(pyatspi.STATE_SHOWING):
            continue
        yield node
        try:
            queue.extend((node[i], depth + 1) for i in range(node.childCount))
        except (LookupError, RuntimeError):
            pass


def find(name=None, role=None):
    # Return immediately: Qt transient list items can expire during a full walk.
    for node in nodes():
        if (name is None or node.name == name) and (role is None or node.getRoleName() == role):
            if node.getState().contains(pyatspi.STATE_SHOWING):
                return node
    raise AssertionError(f'Visible accessible control missing: {name!r} / {role}')


def click(name, role=None):
    node = find(name, role)
    rect = node.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    assert rect.width > 0 and rect.height > 0
    desktop_input('mousemove', str(rect.x + rect.width // 2), str(rect.y + rect.height // 2), 'click', '1')
    time.sleep(.4)


def snapshot(name):
    rows = []
    for node in nodes():
        if node.getState().contains(pyatspi.STATE_SHOWING):
            rows.append({'name': node.name, 'role': node.getRoleName()})
    (E / (name + '-accessibility.json')).write_text(json.dumps(rows, indent=2))
    return rows


def environment():
    sockets = [p for p in Path('/tmp/.X11-unix').glob('X*') if p.name != 'X99']
    assert sockets, 'KWin Xwayland socket missing'
    env = {**os.environ, 'QT_QPA_PLATFORM': 'xcb', 'DISPLAY': ':' + sockets[0].name[1:]}
    auth = list(Path(os.environ['XDG_RUNTIME_DIR']).glob('xauth*')) + list(Path('/tmp').glob('xauth*'))
    if auth:
        env['XAUTHORITY'] = str(auth[0])
    return env


def window(app):
    for _ in range(40):
        assert app.poll() is None, 'Settings exited before showing a window'
        query = subprocess.run(['xdotool', 'search', '--onlyvisible', '--pid', str(app.pid)], env=ENV, text=True, capture_output=True)
        if query.returncode == 0 and query.stdout.strip():
            return query.stdout.splitlines()[-1]
        time.sleep(.5)
    raise AssertionError('Visible native Settings window timed out')


def launch(module):
    log = (E / ((module or 'settings-main') + '.log')).open('w')
    app = subprocess.Popen(['systemsettings'] + ([module] if module else []), env=ENV, stdout=log, stderr=subprocess.STDOUT)
    children.append(app)
    window(app)
    time.sleep(2)
    return app


def focus_title(app):
    identifier = window(app)
    run('xdotool', 'windowactivate', '--sync', identifier, env=ENV)
    raw = run('xdotool', 'getwindowgeometry', '--shell', identifier, env=ENV)
    geometry = dict(line.split('=', 1) for line in raw.splitlines())
    assert int(geometry['Y']) > 25, 'Expected decorated QA window'
    desktop_input('mousemove', str(int(geometry['X']) + int(geometry['WIDTH']) // 2), str(int(geometry['Y']) - 15), 'click', '1')


def close(app):
    focus_title(app)
    desktop_input('key', '--clearmodifiers', 'alt+F4')
    app.wait(timeout=10)


def scenario(name, fn):
    before = time.monotonic()
    try:
        value = {'name': name, 'status': 'passed', 'detail': fn()}
    except Exception as error:
        value = {'name': name, 'status': 'failed', 'error': type(error).__name__ + ': ' + str(error)}
        snapshot(name + '-failure')
    value['seconds'] = round(time.monotonic() - before, 2)
    results.append(value)
    shot(name)
    print(json.dumps(value), flush=True)
    if value['status'] == 'failed':
        desktop_input('key', 'Escape')
    for child in children:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)


def page(module, label):
    app = launch(module)
    rows = snapshot(label)
    shot(label + '-open')
    assert any(r['role'] == 'application' for r in rows)
    if module == 'kcm_bluetooth':
        assert any('No Bluetooth adapters found' in r['name'] for r in rows)
    close(app)
    time.sleep(.5)
    shot(label + '-closed')
    return {'module': module, 'open_close': True, 'physical_connection_tested': False}


def search():
    app = launch('')
    focus_title(app)
    raw = run('xdotool', 'getwindowgeometry', '--shell', window(app), env=ENV)
    geometry = dict(line.split('=', 1) for line in raw.splitlines())
    # The main Qt Quick sidebar reports unreliable desktop coordinates through
    # AT-SPI in this nested fixture. Target its observed client-relative position.
    desktop_input('mousemove', str(int(geometry['X']) + 100), str(int(geometry['Y']) + 24), 'click', '1')
    desktop_input('type', '--clearmodifiers', 'Bluetooth')
    time.sleep(2)
    field = next((n for n in nodes() if n.name == 'Search' and n.getRoleName() == 'text' and n.queryText().getText(0, -1) == 'Bluetooth'), None)
    assert field is not None, 'Bluetooth query did not reach the native Settings search field'
    find('Bluetooth', 'list item')
    shot('03-settings-search-results')
    snapshot('03-settings-search-results')
    desktop_input('key', 'ctrl+a', 'BackSpace')
    time.sleep(.5)
    assert not field.queryText().getText(0, -1), 'Search did not clear'
    shot('03-settings-search-cleared')
    close(app)
    return {'query': 'Bluetooth', 'matching_result_visible': True, 'clear_verified': True}


def password():
    before = run('nmcli', '-t', '-f', 'UUID', 'connection', 'show')
    assert not before, 'Expected empty private NetworkManager fixture'
    app = launch('kcm_networkmanagement')
    # Add's stable Qt action exposes the native chooser without saving anything.
    assert find('Add new connection', 'button').queryAction().doAction(0)
    time.sleep(.5)
    shot('04-connection-types')
    click('Wi-Fi', 'list item')
    time.sleep(1)
    click('Wi-Fi Security', 'page tab')
    shot('05-wifi-security')
    # The combo has a buddy label; inspect only this known empty test form.
    combo = find('None', 'combo box')
    rect = combo.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    desktop_input('mousemove', str(rect.x + rect.width // 2), str(rect.y + rect.height // 2), 'click', '1')
    desktop_input('key', 'Home', 'Down', 'Down', 'Down', 'Down', 'Down', 'Return')
    time.sleep(.5)
    find('WPA/WPA2 Personal', 'combo box')
    field = find(role='password text')
    rect = field.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    desktop_input('mousemove', str(rect.x + 35), str(rect.y + rect.height // 2), 'click', '1')
    desktop_input('type', '--clearmodifiers', 'OREZ-QA-Dummy-Only')
    time.sleep(.5)
    shot('06-dummy-password-masked')
    # Use the actual reveal button; only the deliberate dummy value is captured.
    desktop_input('mousemove', str(rect.x + rect.width - 15), str(rect.y + rect.height // 2), 'click', '1')
    time.sleep(.3)
    revealed = next((n for n in nodes() if n.getRoleName() == 'text' and n.queryText().getText(0, -1) == 'OREZ-QA-Dummy-Only'), None)
    assert revealed is not None, 'Dummy password was not revealed'
    shot('07-dummy-password-revealed')
    desktop_input('mousemove', str(rect.x + rect.width - 15), str(rect.y + rect.height // 2), 'click', '1')
    field = find(role='password text')
    rect = field.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
    desktop_input('mousemove', str(rect.x + 35), str(rect.y + rect.height // 2), 'click', '1')
    desktop_input('key', 'ctrl+a', 'BackSpace')
    assert field.queryText().characterCount == 0
    shot('08-dummy-password-cleared')
    click('Cancel', 'button')
    time.sleep(.5)
    assert run('nmcli', '-t', '-f', 'UUID', 'connection', 'show') == before
    shot('09-connection-cancelled')
    close(app)
    return {'dummy_only': True, 'masked_revealed_remasked_cleared': True, 'cancel_saved_no_connection': True, 'wifi_authentication_tested': False}


def main():
    global ENV
    ENV = environment()
    (E / 'session-environment.json').write_text(json.dumps({k: ENV.get(k) for k in ['DBUS_SESSION_BUS_ADDRESS', 'DISPLAY', 'XAUTHORITY', 'XDG_RUNTIME_DIR', 'WAYLAND_DISPLAY']}, indent=2))
    try:
        scenario('01-native-network-settings', lambda: page('kcm_networkmanagement', '01-network'))
        scenario('02-native-bluetooth-settings', lambda: page('kcm_bluetooth', '02-bluetooth'))
        scenario('03-native-settings-search', search)
        scenario('04-native-dummy-password', password)
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        (E / 'connectivity-results.json').write_text(json.dumps({'hardware_tested': False, 'scenarios': results}, indent=2) + '\n')
    raise SystemExit(any(r['status'] == 'failed' for r in results))


if __name__ == '__main__':
    main()
