"""Actual APT failure, upgrade and rollback scenarios in a disposable container.

Versioned fixtures are deliberately local test packages, not published releases.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

assert os.getuid() == 0 and Path('/.dockerenv').exists() and os.environ.get('OREZ_DISPOSABLE_TEST') == '1'
EVIDENCE = Path('/evidence')
EVIDENCE.mkdir(exist_ok=True)
ROOT = Path('/tmp/orez-package-scenarios')
ROOT.mkdir()
APT = ['apt-get', '-y', '-o', 'Dpkg::Options::=--path-include=/usr/share/doc/orez', '-o', 'Dpkg::Options::=--path-include=/usr/share/doc/orez/*']
results = []


def run(args, *, expected=0):
    result = subprocess.run(args, text=True, capture_output=True, timeout=45)
    with (EVIDENCE / 'package-scenarios.log').open('a') as log:
        log.write('\nCOMMAND: ' + repr(args) + '\n' + result.stdout + result.stderr)
    if expected == 0 and result.returncode != 0:
        raise AssertionError(f'{args}: exit {result.returncode}: {result.stderr[-1500:]}')
    if expected == 'failure' and result.returncode == 0:
        raise AssertionError('unexpected success: ' + repr(args))
    return result


def version():
    return run(['dpkg-query', '-W', '-f=${Version}', 'orez-shell']).stdout.strip()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture(suffix, marker, dependency=None):
    stage = ROOT / suffix
    run(['dpkg-deb', '--raw-extract', '/input/orez-shell.deb', str(stage)])
    control = stage / 'DEBIAN/control'
    text = control.read_text().replace('Version: 0.1.0-1', 'Version: 0.1.0-1+' + suffix)
    if dependency:
        text = '\n'.join('Depends: ' + dependency if line.startswith('Depends:') else line for line in text.splitlines()) + '\n'
    control.write_text(text)
    identity = stage / 'etc/orez-release'
    identity.write_text(identity.read_text() + '\nOREZ_QA_FIXTURE=' + marker + '\n')
    output = ROOT / (suffix + '.deb')
    run(['dpkg-deb', '--build', '--root-owner-group', str(stage), str(output)])
    return output, sha(identity)


one, hash_one = fixture('qatest.1', 'one')
two, hash_two = fixture('qatest.2', 'two')
bad_dependency, _ = fixture('qatest.3', 'bad-dependency', 'orez-qa-package-that-does-not-exist (= 999)')
corrupt = ROOT / 'corrupt.deb'
corrupt.write_bytes(one.read_bytes()[:80])
home = Path('/home/orez-test')
sentinel = home / 'retain-project.txt'
sentinel.write_text('Unrelated user data must survive upgrades and purge')
os.chown(sentinel, 1500, 1500)
sentinel_hash = sha(sentinel)


def state(expected, digest):
    assert version() == expected
    assert sha('/etc/orez-release') == digest
    assert sha(sentinel) == sentinel_hash
    assert not run(['dpkg', '--audit']).stdout.strip()


def scenario(name, function):
    before = time.monotonic()
    try:
        detail = function()
        result = {'name': name, 'status': 'passed', 'detail': detail}
    except Exception as error:
        result = {'name': name, 'status': 'failed', 'detail': str(error)}
    result['seconds'] = round(time.monotonic() - before, 3)
    results.append(result)
    print(json.dumps(result), flush=True)
    # Later stateful upgrade cases require the preceding assertion to hold.
    if result['status'] == 'failed':
        save()
        raise SystemExit(1)


def save():
    (EVIDENCE / 'package-scenarios.json').write_text(json.dumps({'fixture_versions': True, 'installation_approved': False, 'scenarios': results}, indent=2))


def initial():
    run(APT + ['install', str(one)])
    state('0.1.0-1+qatest.1', hash_one)
    return 'Actual first fixture installed and payload hash matched'


def denied_user():
    run(['runuser', '-u', 'orez-test', '--', 'dpkg', '-i', str(two)], expected='failure')
    state('0.1.0-1+qatest.1', hash_one)
    return 'Ordinary-user dpkg installation denied without modifying current package'


def preference():
    run(['runuser', '-u', 'orez-test', '--', 'env', 'HOME=/home/orez-test', 'orezctl', 'appearance', 'disable'])
    assert 'Hidden=true' in (home / '.config/autostart/orez-initialize.desktop').read_text()
    return 'Per-user opt-out configured for upgrade preservation tests'


def bad_archive():
    run(APT + ['install', str(corrupt)], expected='failure')
    state('0.1.0-1+qatest.1', hash_one)
    return 'Truncated package rejected; installed version, payload and unrelated data unchanged'


def dependency_failure():
    run(APT + ['install', str(bad_dependency)], expected='failure')
    state('0.1.0-1+qatest.1', hash_one)
    return 'Unresolvable dependency rejected without breaking dpkg state'


def upgrade():
    run(APT + ['install', str(two)])
    state('0.1.0-1+qatest.2', hash_two)
    assert 'Hidden=true' in (home / '.config/autostart/orez-initialize.desktop').read_text()
    return 'Newer local fixture installed; expected changed payload and user opt-out both verified'


def refused_downgrade():
    run(APT + ['install', str(one)], expected='failure')
    state('0.1.0-1+qatest.2', hash_two)
    return 'APT refused unattended downgrade without explicit --allow-downgrades'


def rollback():
    run(APT + ['--allow-downgrades', 'install', str(one)])
    state('0.1.0-1+qatest.1', hash_one)
    assert 'Hidden=true' in (home / '.config/autostart/orez-initialize.desktop').read_text()
    return 'Explicit package downgrade restored earlier payload while retaining user preference and files'


def purge():
    run(APT + ['purge', 'orez-shell'])
    assert not Path('/usr/bin/orezctl').exists()
    assert not Path('/etc/orez-release').exists()
    assert sha(sentinel) == sentinel_hash
    assert 'Hidden=true' in (home / '.config/autostart/orez-initialize.desktop').read_text()
    assert not run(['dpkg', '--audit']).stdout.strip()
    return 'Purge removed package but retained user data and deliberate user opt-out'


def return_after_purge():
    run(APT + ['install', str(two)])
    state('0.1.0-1+qatest.2', hash_two)
    assert 'Hidden=true' in run(['runuser', '-u', 'orez-test', '--', 'cat', str(home / '.config/autostart/orez-initialize.desktop')]).stdout
    return 'Fresh installation after purge retained user control and restored correct payload'


for name, function in [('initial fixture install', initial), ('non-admin install rejected', denied_user),
                       ('user opt-out', preference), ('corrupt archive rejected', bad_archive),
                       ('unmet dependency rejected', dependency_failure), ('newer version upgrade', upgrade),
                       ('implicit downgrade rejected', refused_downgrade), ('explicit package rollback', rollback),
                       ('purge preserves user state', purge), ('reinstall after purge', return_after_purge)]:
    scenario(name, function)
save()
