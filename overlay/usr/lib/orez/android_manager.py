#!/usr/bin/env python3
"""Unprivileged, opt-in Android SDK/Google Play AVD manager.

Google software is downloaded from its official source after interactive
licence acceptance, never bundled in OREZ. No root, boot changes or autostart.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

IMAGE = 'system-images;android-36;google_apis_playstore;x86_64'
AVD = 'OREZ_Play'
TOOLS_URL = 'https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip'
# Published on https://developer.android.com/studio, checked 2026-11-05.
TOOLS_SHA256 = '4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583'
TERMS_URL = 'https://developer.android.com/studio/terms'
DELETE_CONFIRMATION = 'DELETE OREZ ANDROID DATA'

# Reviewed aliases only. No arbitrary shell commands, APK URLs or attached phones.
APP_PACKAGES = {
    'youtube': 'com.google.android.youtube', 'instagram': 'com.instagram.android',
    'brave': 'com.brave.browser', 'chrome': 'com.android.chrome',
    'subway-surfers': 'com.kiloo.subwaysurf', 'free-fire': 'com.dts.freefireth',
    'asphalt-legends': 'com.gameloft.android.ANMP.GloftA9HM', 'play-store': 'com.android.vending',
}


def memory_budget():
    values = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, _, value = line.partition(':')
        if key in ['MemTotal', 'MemAvailable']:
            values[key] = int(value.split()[0]) * 1024
    total = values['MemTotal']; available = values.get('MemAvailable', 0)
    limit = Path('/sys/fs/cgroup/memory.max'); used = Path('/sys/fs/cgroup/memory.current')
    if limit.exists() and used.exists():
        bound = limit.read_text().strip()
        if bound.isdigit():
            total = min(total, int(bound))
            available = min(available, max(0, int(bound) - int(used.read_text())))
    return {'total_mb': total // 1048576, 'available_mb': available // 1048576}


class Manager:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'orez/android'
        self.sdk = self.root / 'sdk'
        self.avds = self.root / 'avd'
        self.profile = self.avds / (AVD + '.avd')
        self.logs = self.root / 'logs'
        self.config_file = self.root / 'config.json'
        self.state_file = self.root / 'running.json'

    def prepare(self):
        if os.getuid() == 0:
            raise ValueError('Run Android Apps as your normal desktop user, never root.')
        # Refuse an aliased managed directory before downloads or removals.
        for path in [self.root, *self.root.parents]:
            if path.is_symlink():
                raise ValueError('The managed Android path must not contain symlinks.')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.stat().st_uid != os.getuid():
            raise ValueError('Android data directory is not owned by this user.')
        marker = self.root / '.orez-managed'
        if marker.is_symlink() or (not marker.exists() and any(self.root.iterdir())):
            raise ValueError('Existing unrecognized Android storage will not be adopted or erased.')
        os.chmod(self.root, 0o700)
        for path in [self.sdk, self.avds, self.logs]:
            if path.is_symlink():
                raise ValueError('Refusing a symlink in managed Android storage.')
            path.mkdir(exist_ok=True, mode=0o700)
        if not marker.exists():
            self.write_json(marker, {'version': 1, 'owner_uid': os.getuid()})

    @staticmethod
    def write_json(path, data):
        if path.is_symlink():
            raise ValueError('Refusing to write through a symlink.')
        temporary = path.with_name(path.name + '.new')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(data, stream, indent=2)
                stream.write('\n')
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def configuration(self):
        data = {'memory_mb': 2048 if memory_budget()['total_mb'] < 8192 else 3072, 'cores': 2, 'graphics': 'software'}
        if self.config_file.exists():
            value = json.loads(self.config_file.read_text())
            if not isinstance(value, dict) or set(value) - set(data):
                raise ValueError('Invalid Android settings; reset the settings file using the documented path.')
            data.update(value)
        if type(data['memory_mb']) is not int or data['memory_mb'] not in [2048, 3072, 4096]:
            raise ValueError('Memory must be 2048, 3072 or 4096 MiB.')
        if type(data['cores']) is not int or data['cores'] not in [1, 2, 4]:
            raise ValueError('CPU count must be 1, 2 or 4.')
        if data['graphics'] not in ['software', 'auto']:
            raise ValueError('Graphics must be software or auto.')
        return data

    def environment(self):
        return {**os.environ, 'ANDROID_HOME': str(self.sdk), 'ANDROID_SDK_ROOT': str(self.sdk),
                'ANDROID_USER_HOME': str(self.root / 'android-user'), 'ANDROID_AVD_HOME': str(self.avds),
                'ANDROID_ADB_SERVER_PORT': '5038', 'ADB_SERVER_SOCKET': 'tcp:localhost:5038'}

    def audit(self, action, detail):
        self.prepare()
        path = self.logs / 'actions.jsonl'
        if path.is_symlink():
            raise ValueError('Refusing a symlink log.')
        with path.open('a') as log:
            log.write(json.dumps({'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'action': action, 'detail': detail}) + '\n')
        os.chmod(path, 0o600)

    def status(self):
        ancestor = self.root
        while not ancestor.exists():
            ancestor = ancestor.parent
        return {'provider': 'Official Android Emulator — development/testing provider', 'system_image': IMAGE,
                'installed': (self.sdk / 'emulator/emulator').is_file(), 'profile_exists': self.profile.is_dir(),
                'kvm_available': os.access('/dev/kvm', os.R_OK | os.W_OK), 'architecture': platform.machine(),
                'java_available': bool(shutil.which('java')), 'data_directory': str(self.root),
                'free_gib': round(shutil.disk_usage(ancestor).free / 2**30, 1), 'configuration': self.configuration(),
                'host_memory_budget': memory_budget(),
                'running': self.owned_process() is not None, 'logs': str(self.logs), 'autostart': False,
                'google_account': 'Sign in only inside the emulator. OREZ never requests Google credentials.',
                'compatibility': 'Play Store installation and games require real AVD/hardware validation; ARM-only/DRM/anti-cheat apps may refuse emulators.'}

    def bootstrap(self):
        self.prepare()
        if platform.machine() != 'x86_64':
            raise ValueError('This initial provider supports Linux x86-64 only.')
        if not shutil.which('java'):
            raise ValueError('Install a supported Java runtime through your system package manager (OpenJDK 21 recommended), then retry. No administrator action is automatic.')
        if shutil.disk_usage(self.root).free < 15 * 2**30:
            raise ValueError('At least 15 GiB free is required for SDK download, extraction and Android storage.')
        target = self.sdk / 'cmdline-tools/orez-pinned'
        if (target / 'bin/sdkmanager').is_file():
            return
        print('Google Android SDK terms: ' + TERMS_URL)
        print('This is a development/testing provider. Google software is not redistributed by OREZ.')
        if input('Read the linked terms. Type ACCEPT to download the official SDK, or anything else to cancel: ').strip() != 'ACCEPT':
            raise ValueError('SDK installation cancelled; licence not accepted.')
        self.audit('sdk-license-consent', {'terms': TERMS_URL, 'bootstrap_sha256': TOOLS_SHA256})
        archive = self.root / 'command-tools.download'
        if archive.is_symlink():
            raise ValueError('Refusing a symlink download target.')
        try:
            digest = hashlib.sha256()
            with urllib.request.urlopen(TOOLS_URL, timeout=30) as response, archive.open('wb') as output:
                if not response.url.startswith('https://dl.google.com/android/repository/'):
                    raise ValueError('Unexpected SDK download redirect.')
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > 250 * 1024 * 1024:
                        raise ValueError('Unexpected SDK archive size.')
                    output.write(chunk); digest.update(chunk)
                    print(f'Command tools: {total // 1048576} MiB downloaded', end='\r', flush=True)
            if digest.hexdigest() != TOOLS_SHA256:
                raise ValueError('Official SDK checksum mismatch; refusing to execute it.')
            with tempfile.TemporaryDirectory(dir=self.root, prefix='extract-') as stage:
                self.extract_tools(archive, Path(stage))
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise ValueError('Partial SDK tools directory exists; inspect it before retrying.')
                (Path(stage) / 'cmdline-tools').rename(target)
            self.audit('sdk-bootstrap', {'sha256': digest.hexdigest()})
        finally:
            archive.unlink(missing_ok=True)

    @staticmethod
    def extract_tools(archive, target):
        with zipfile.ZipFile(archive) as data:
            if sum(item.file_size for item in data.infolist()) > 1024**3:
                raise ValueError('SDK expanded size exceeds limit.')
            for item in data.infolist():
                parts = Path(item.filename).parts
                if not parts or parts[0] != 'cmdline-tools' or '..' in parts or '\\' in item.filename or stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError('Unsafe path or symlink in SDK archive.')
                data.extract(item, target)
                path = target / item.filename
                os.chmod(path, 0o755 if item.is_dir() or '/bin/' in item.filename else 0o644)

    def setup(self):
        self.bootstrap()
        print('\nGoogle SDK Manager will now display any additional licence prompts. Read and answer them yourself.')
        manager = self.sdk / 'cmdline-tools/orez-pinned/bin/sdkmanager'
        subprocess.run([str(manager), '--sdk_root=' + str(self.sdk), 'platform-tools', 'emulator', IMAGE], env=self.environment(), check=True)
        self.create()
        self.audit('sdk-install', {'image': IMAGE, 'source_properties': {str(p.relative_to(self.sdk)): p.read_text() for p in self.sdk.rglob('source.properties')}})

    def create(self):
        self.prepare()
        if self.profile.exists() or (self.avds / (AVD + '.ini')).exists():
            raise ValueError('The OREZ Android profile already exists. Setup will not overwrite its data.')
        manager = self.sdk / 'cmdline-tools/orez-pinned/bin/avdmanager'
        subprocess.run([str(manager), 'create', 'avd', '--name', AVD, '--package', IMAGE,
                        '--device', 'pixel_5', '--path', str(self.profile)], input='no\n', text=True,
                       env=self.environment(), check=True)
        self.audit('profile-created', {'name': AVD, 'image': IMAGE})

    def launch_plan(self):
        config = self.configuration()
        return [str(self.sdk / 'emulator/emulator'), '-avd', AVD, '-accel', 'on',
                '-memory', str(config['memory_mb']), '-cores', str(config['cores']), '-gpu', config['graphics'],
                '-port', '5556', '-no-snapshot', '-no-boot-anim']

    def owned_process(self):
        if not self.state_file.exists():
            return None
        try:
            state = json.loads(self.state_file.read_text())
            pid = state['pid']; proc = Path('/proc') / str(pid)
            if type(pid) is not int or pid < 2 or proc.stat().st_uid != os.getuid():
                return None
            ticks = proc.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19]
            argv = proc.joinpath('cmdline').read_bytes().split(b'\0')
            exe = proc.joinpath('exe').resolve()
            if ticks != state['start_ticks'] or not exe.is_relative_to((self.sdk / 'emulator').resolve()):
                return None
            if b'-avd' not in argv or argv[argv.index(b'-avd') + 1] != AVD.encode() or os.getpgid(pid) != pid:
                return None
            return pid
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            return None

    def start(self):
        self.prepare()
        if self.owned_process():
            raise ValueError('OREZ Android is already running.')
        if not os.access('/dev/kvm', os.R_OK | os.W_OK):
            raise ValueError('KVM is unavailable to your user. Enable AMD SVM in firmware and have an administrator configure KVM access, then log in again. OREZ will not modify firmware/groups or silently use slow emulation.')
        if not self.profile.is_dir():
            raise ValueError('Use Setup before starting Android Apps.')
        if memory_budget()['available_mb'] < self.configuration()['memory_mb'] + 2048:
            raise ValueError('Not enough available memory to leave 2 GiB for the host. Close applications or lower Android memory in Settings before starting.')
        with (self.logs / 'emulator.log').open('a') as log:
            process = subprocess.Popen(self.launch_plan(), env=self.environment(), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(1)
        if process.poll() is not None:
            raise ValueError('The emulator exited. Inspect ' + str(self.logs / 'emulator.log'))
        ticks = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
        self.write_json(self.state_file, {'pid': process.pid, 'start_ticks': ticks})
        self.audit('start', {'configuration': self.configuration()})

    def stop(self):
        pid = self.owned_process()
        if pid:
            os.killpg(pid, signal.SIGTERM)
            for _ in range(50):
                if self.owned_process() is None:
                    break
                time.sleep(.1)
            else:
                os.killpg(pid, signal.SIGKILL)
        self.state_file.unlink(missing_ok=True)
        self.audit('stop', {'owned_process_was_running': bool(pid)})

    def app_command(self, app, action, development_test=False):
        """Build a narrowly scoped guest request; never target a phone or host shell.

        The existing SDK provider remains development/testing only. An explicit
        flag is an operation acknowledgement, not a consumer-use licence grant.
        """
        if os.getuid() == 0 or os.geteuid() == 0:
            raise ValueError('Android app operations must run as the ordinary user.')
        if app not in APP_PACKAGES or action not in ['app-status','open-app','store-page','app-settings']:
            raise ValueError('Unknown Android app or operation.')
        if not development_test:
            raise ValueError('Consumer runtime is not qualified. The existing SDK provider is development/testing only.')
        if not self.owned_process():
            raise ValueError('Start the owned OREZ Android development emulator first; no other device will be contacted.')
        self.prepare()
        adb=self.sdk/'platform-tools/adb'
        if not adb.is_file() or adb.is_symlink():
            raise ValueError('Managed SDK ADB is missing or aliased.')
        base=[str(adb),'-H','127.0.0.1','-P','5038','-s','emulator-5556']
        name=subprocess.run(base+['emu','avd','name'],env=self.environment(),capture_output=True,text=True,timeout=15,check=True).stdout.splitlines()
        if not name or name[0].strip()!=AVD:
            raise ValueError('The selected emulator does not match the owned OREZ profile.')
        package=APP_PACKAGES[app]
        if action=='app-status': return base+['shell','pm','path',package]
        if action=='store-page':
            return base+['shell','am','start','-W','-a','android.intent.action.VIEW','-d',
                         'market://details?id='+package,'-p','com.android.vending']
        if action=='app-settings':
            return base+['shell','am','start','-W','-a','android.settings.APPLICATION_DETAILS_SETTINGS','-d','package:'+package]
        component=subprocess.run(base+['shell','cmd','package','resolve-activity','--brief','-a',
                   'android.intent.action.MAIN','-c','android.intent.category.LAUNCHER',package],
                   env=self.environment(),capture_output=True,text=True,timeout=15,check=True).stdout.strip().splitlines()
        candidate=component[-1] if component else ''
        if not re.fullmatch(re.escape(package)+r'/[A-Za-z0-9_.$]+',candidate):
            raise ValueError('App is not installed or its launcher did not match the requested package.')
        return base+['shell','am','start','-W','-n',candidate]

    def app_action(self, app, action, development_test=False):
        command=self.app_command(app,action,development_test)
        result=subprocess.run(command,env=self.environment(),capture_output=True,text=True,timeout=30,check=True)
        if action=='app-status':
            return {'app':app,'package':APP_PACKAGES[app],
                    'installed':any(line.startswith('package:') for line in result.stdout.splitlines()),
                    'provider':'development/testing SDK', 'compatibility_verified':False}
        if 'Error:' in result.stdout or 'Error:' in result.stderr or 'Exception' in result.stdout+result.stderr:
            raise ValueError('Android rejected the request. Check its installation, Play Store and permissions inside the guest.')
        self.audit(action,{'app':app,'package':APP_PACKAGES[app]})
        return {'app':app,'action':action,'request_delivered':True,'compatibility_verified':False,
                'purchase_authorized':False,'installation_claimed':False}

    def destroy(self, all_runtime, confirmation):
        if confirmation != DELETE_CONFIRMATION:
            raise ValueError('Destructive action requires the exact confirmation phrase.')
        self.prepare()
        marker = json.loads((self.root / '.orez-managed').read_text())
        if marker.get('owner_uid') != os.getuid():
            raise ValueError('Managed directory ownership marker differs.')
        self.stop()
        targets = [self.avds, self.sdk, self.root / 'android-user'] if all_runtime else [self.profile, self.avds / (AVD + '.ini')]
        for path in targets:
            if path.is_symlink() or not path.resolve().is_relative_to(self.root.resolve()):
                raise ValueError('Refusing an aliased or external deletion target.')
        for path in targets:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
        self.audit('remove-runtime' if all_runtime else 'reset-profile', {'account_and_app_data_deleted': True})
        if not all_runtime:
            self.create()


def gui(manager):
    title = ['kdialog', '--title', 'OREZ Android Apps']
    while True:
        result = subprocess.run(title + ['--menu', 'Optional Google Play development emulator. Apps/games and hardware support still require qualification.',
            'status', 'Status, effective settings and requirements', 'setup', 'Download/setup official Android tools (licence prompts)',
            'start', 'Start Android / Play Store', 'stop', 'Stop Android (emergency stop)', 'configure', 'Memory and graphics',
            'logs', 'Open logs', 'reset', 'Reset Android — erase apps/account data', 'remove', 'Remove Android runtime and its data'], capture_output=True, text=True)
        if result.returncode:
            return
        action = result.stdout.strip()
        try:
            if action == 'status':
                subprocess.run(title + ['--msgbox', json.dumps(manager.status(), indent=2)], check=True)
            elif action == 'setup':
                subprocess.Popen(['konsole', '--separate', '--hold', '-e', '/usr/bin/orez-android', 'setup'])
            elif action == 'configure':
                memory = subprocess.check_output(title + ['--combobox', 'Android memory (MiB)', '3072', '2048', '4096'], text=True).strip()
                graphics = subprocess.check_output(title + ['--combobox', 'Graphics: software is conservative; auto must be tested on your NVIDIA GPU.', 'software', 'auto'], text=True).strip()
                manager.prepare(); config = manager.configuration(); config.update(memory_mb=int(memory), graphics=graphics)
                manager.write_json(manager.config_file, config); manager.audit('configure', config)
            elif action == 'logs':
                manager.prepare(); subprocess.Popen(['xdg-open', str(manager.logs)])
            elif action in ['reset', 'remove']:
                consent = subprocess.run(title + ['--warningyesno', 'Permanently erase the OREZ Android profile, Google account session and app data? This affects only the managed emulator. ' + ('The SDK is also removed.' if action == 'remove' else 'The profile will be recreated.')])
                if consent.returncode == 0:
                    manager.destroy(action == 'remove', DELETE_CONFIRMATION)
            elif action == 'start':
                manager.start()
            elif action == 'stop':
                manager.stop()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            subprocess.run(title + ['--error', str(error)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='gui', choices=['gui', 'status', 'setup', 'create', 'start', 'stop', 'launch-plan', 'reset', 'remove', 'app-status', 'open-app', 'store-page', 'app-settings'])
    parser.add_argument('--confirm', default='')
    parser.add_argument('--app', choices=sorted(APP_PACKAGES))
    parser.add_argument('--development-test', action='store_true')
    args = parser.parse_args(); manager = Manager()
    try:
        if args.action in ['app-status','open-app','store-page','app-settings']:
            if not args.app: parser.error('--app is required')
            print(json.dumps(manager.app_action(args.app,args.action,args.development_test),indent=2))
        elif args.action == 'gui': gui(manager)
        elif args.action == 'status': print(json.dumps(manager.status(), indent=2))
        elif args.action == 'launch-plan': print(json.dumps(manager.launch_plan(), indent=2))
        elif args.action in ['reset', 'remove']: manager.destroy(args.action == 'remove', args.confirm)
        else: getattr(manager, args.action)()
        return 0
    except (OSError, ValueError, EOFError, subprocess.SubprocessError) as error:
        print('OREZ Android Apps: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
