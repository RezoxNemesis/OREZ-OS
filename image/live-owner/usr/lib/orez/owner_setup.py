#!/usr/bin/env python3
"""Local, console-only owner enrollment for a volatile OREZ live session.

Not a remote service, installer or normal desktop package component. The initrd
creates a locked owner and root-owned request. SDDM must depend on successful
completion. Passwords are read without echo and passed only through stdin to
the system password utility. No environment/CLI bypass or default password.
"""
import getpass
import grp
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys
import time
import warnings

REQUEST = Path('/var/lib/orez-live/owner-required')
READY = Path('/run/orez-live/owner-ready.json')
SUDOERS = Path('/etc/sudoers.d/orez-live-owner')
PLYMOUTH_PID = Path('/run/plymouth/pid')


def root_file(path, mode):
    for parent in path.parents:
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('Untrusted setup directory: ' + str(parent))
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != mode:
        raise ValueError('Untrusted setup file: ' + str(path))


def require_live():
    if os.getuid() != 0 or os.geteuid() != 0:
        raise ValueError('Owner enrollment is a boot service, not a user command.')
    tokens = Path('/proc/cmdline').read_text().split()
    if 'boot=casper' not in tokens or any(t == 'persistent' or t.startswith('persistent=') for t in tokens):
        raise ValueError('Owner enrollment requires a nonpersistent casper live boot.')


def run(args, data=None):
    # No shell, inherited user PATH, passwords in argv, or command-output logs.
    result = subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=20, env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8'})
    if result.returncode:
        raise ValueError('System account operation failed; desktop remains blocked.')
    return result.stdout


def shadow_state(username):
    root_file(Path('/etc/shadow'), 0o640)
    entries = dict((line.split(':', 2)[0], line.split(':', 2)[1])
                   for line in Path('/etc/shadow').read_text().splitlines() if ':' in line)
    if not entries.get('root', '').startswith(('!', '*')):
        raise ValueError('Direct root login must remain locked.')
    if username not in entries:
        raise ValueError('Owner account not found.')
    return entries[username]


def validate_owner(username, locked=True):
    if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,30}', username):
        raise ValueError('Invalid live owner name.')
    account = pwd.getpwnam(username)
    if account.pw_uid != 1000 or account.pw_shell not in ['/bin/bash', '/bin/sh']:
        raise ValueError('Unexpected live owner account.')
    admins = grp.getgrnam('sudo')
    if set(admins.gr_mem) != {username} or any(
            p.pw_gid == admins.gr_gid and p.pw_name != username for p in pwd.getpwall()):
        raise ValueError('Only the live owner may belong to the sudo administrator group.')
    value = shadow_state(username)
    if locked and not value.startswith(('!', '*')):
        raise ValueError('Enrollment will not replace an existing owner password.')
    if not locked and (not value or value.startswith(('!', '*'))):
        raise ValueError('Owner authentication is not ready.')
    root_file(SUDOERS, 0o440)
    if SUDOERS.read_text() != 'Defaults:%sudo timestamp_timeout=0\n':
        raise ValueError('Unexpected owner authentication policy.')
    run(['/usr/sbin/visudo', '-c'])


def validate_password(password):
    if not 12 <= len(password) <= 128 or any(ord(c) < 32 or ord(c) == 127 for c in password):
        raise ValueError('Use 12–128 characters without control characters.')


def process_identity(pid):
    try:
        fields = Path('/proc/' + str(pid) + '/stat').read_text().rpartition(')')[2].split()
        return None if fields[0] == 'Z' else fields[19]
    except FileNotFoundError:
        return None


def prepare_console():
    # A quit request alone need not mean the daemon has closed its TTY. Wait
    # for shutdown before getpass changes echo; never kill an arbitrary PID.
    pid = identity = None
    try:
        mode = stat.S_IMODE(PLYMOUTH_PID.lstat().st_mode)
        if mode & 0o022:
            raise ValueError('Untrusted splash process file.')
        root_file(PLYMOUTH_PID, mode)
        pid = int(PLYMOUTH_PID.read_text().strip())
        if pid <= 1:
            raise ValueError('Invalid splash process identity.')
        identity = process_identity(pid)
    except FileNotFoundError:
        pass
    def invoke(argument):
        return subprocess.run(['/usr/bin/plymouth', argument], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=20, check=False,
                              env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8'})
    invoke('quit')
    invoke('--wait')
    deadline = time.monotonic() + 20
    while identity is not None and process_identity(pid) == identity:
        if time.monotonic() >= deadline:
            raise ValueError('Boot splash has not released the console. Reboot to retry.')
        time.sleep(.05)
    if invoke('--ping').returncode == 0:
        raise ValueError('Boot splash is still active. Password setup remains blocked.')


def hidden_password(prompt):
    # The stdlib's default fallback warns and then reads with echo enabled.
    # A password-enrollment service must refuse that fallback before reading.
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        try:
            return getpass.getpass(prompt)
        except getpass.GetPassWarning:
            raise ValueError('Cannot hide password input. Reboot verified media and retry.') from None


def private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError('Untrusted completion directory.')


def complete(username, password):
    """Root-only implementation; caller enforces boot state and local console."""
    require_live()
    validate_owner(username)
    validate_password(password)
    private_directory(READY.parent)
    if READY.exists() or READY.is_symlink():
        raise ValueError('Unexpected existing completion record.')
    changed = False
    try:
        changed = True
        run(['/usr/sbin/chpasswd'], username + ':' + password + '\n')
        validate_owner(username, locked=False)
        fd = os.open(READY, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump({'schema': 1, 'username': username, 'uid': 1000, 'session': 'volatile-live'}, stream)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        REQUEST.unlink()
    except Exception:
        READY.unlink(missing_ok=True)
        if changed:
            run(['/usr/sbin/usermod', '--lock', username])
        raise


def enroll():
    require_live()
    if READY.exists():
        root_file(READY, 0o600)
        state = json.loads(READY.read_text())
        if set(state) != {'schema', 'username', 'uid', 'session'} or state['schema'] != 1 or state['uid'] != 1000 or state['session'] != 'volatile-live' or REQUEST.exists():
            raise ValueError('Unexpected live-owner completion state.')
        validate_owner(state['username'], locked=False)
        return
    root_file(REQUEST, 0o600)
    username = REQUEST.read_text().strip()
    validate_owner(username)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError('A local console is required; password input cannot come from a pipe.')
    prepare_console()
    print('\nOREZ OS — Set up this live session\n')
    print('Live owner: ' + username)
    print('Choose a temporary password for login, screen unlock and administrator prompts.')
    print('This is a volatile USB test session. It does not install OREZ or change your SSD.')
    print('The password is not saved on your installation media. Root login stays locked.')
    print('Use 12–128 characters. Input is hidden. Ctrl+C cancels; reboot to restart setup.\n')
    password = hidden_password('New live-session password: ')
    validate_password(password)
    confirmation = hidden_password('Repeat password: ')
    if password != confirmation:
        raise ValueError('Passwords did not match. No password was changed.')
    complete(username, password)
    del password, confirmation
    print('\nOwner setup completed. Continue at the graphical login screen.')


if __name__ == '__main__':
    try:
        enroll()
    except (OSError, ValueError, KeyError, EOFError, KeyboardInterrupt, subprocess.SubprocessError) as error:
        # Never log a password, shadow hash or subprocess input/output.
        print('\nOREZ owner setup stopped: ' + (str(error) or 'Cancelled.') +
              '\nThe desktop remains blocked. Reboot to retry the live session.', file=sys.stderr)
        sys.exit(1)
