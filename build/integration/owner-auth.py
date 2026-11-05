"""Real local account/PAM/sudo checks inside a disposable, offline container.

The live-kernel check is substituted only in the imported test fixture because
this container is not a casper boot. Production CLI denial is tested separately.
No production bypass option exists. No real owner password or hash is recorded.
"""
import hashlib
import json
import os
from pathlib import Path
import pty
import pwd
import secrets
import select
import signal
import subprocess
import sys
import time

assert os.getuid()==0 and Path('/.dockerenv').exists()
OUT=Path(os.environ.get('OREZ_AUTH_EVIDENCE','/evidence/owner-auth'));OUT.mkdir(exist_ok=False)
REQUEST=Path('/var/lib/orez-live/owner-required')
READY=Path('/run/orez-live/owner-ready.json')
USERNAME=pwd.getpwuid(1000).pw_name
SECRET=secrets.token_urlsafe(24)
SCRIPT=Path('/input/owner-console-fixture.py')
SCRIPT.write_text('''import sys
sys.path.insert(0, '/usr/lib/orez')
import owner_setup
# Test-only substitution. All local ownership, terminal and password checks run.
owner_setup.require_live = lambda: None
try:
    owner_setup.enroll()
except (Exception, KeyboardInterrupt):
    print("Fixture enrollment stopped; no credential details logged.")
    sys.exit(1)
''')
results=[]


def command(args, expected=0, input=None):
    result=subprocess.run(args,input=input,capture_output=True,text=True,timeout=20)
    assert result.returncode==expected,(args,result.returncode)
    return result.stdout.strip()


def state():
    shadow={line.split(':',2)[0]:line.split(':',2)[1] for line in Path('/etc/shadow').read_text().splitlines()}
    return {'root_locked':shadow['root'].startswith(('!','*')),
            'owner_locked':shadow[USERNAME].startswith(('!','*')),
            'owner_value':shadow[USERNAME]}


def prepare():
    command(['/usr/sbin/usermod','--lock',USERNAME])
    REQUEST.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    REQUEST.parent.chmod(0o700)
    REQUEST.unlink(missing_ok=True); REQUEST.write_text(USERNAME+'\n'); REQUEST.chmod(0o600)
    READY.unlink(missing_ok=True)
    policy=Path('/etc/sudoers.d/orez-live-owner')
    policy.write_text('Defaults:%sudo timestamp_timeout=0\n');policy.chmod(0o440)
    command(['/usr/sbin/visudo','-c'])


def console(name, answers):
    pid,fd=pty.fork()
    if pid==0:
        os.execv('/usr/bin/python3',['python3','-I',str(SCRIPT)])
    output=b''; sent=0;deadline=time.monotonic()+15
    prompts=[b'New live-session password:',b'Repeat password:']
    status=None
    try:
        while time.monotonic()<deadline:
            if select.select([fd],[],[],.1)[0]:
                try:chunk=os.read(fd,4096)
                except OSError:chunk=b''
                output+=chunk
            if sent<len(answers) and prompts[min(sent,1)] in output:
                os.write(fd,answers[sent]); sent+=1
            waited,code=os.waitpid(pid,os.WNOHANG)
            if waited:
                status=os.waitstatus_to_exitcode(code);break
        assert status is not None,'Enrollment fixture timed out'
        assert sent==len(answers),'Fixture exited before all intended password prompts were exercised'
        assert SECRET.encode() not in output,'Password echoed by console'
        (OUT/(name+'-console.txt')).write_bytes(output)
        return status
    finally:
        os.close(fd)
        if status is None:
            os.kill(pid,signal.SIGKILL);os.waitpid(pid,0)


def scenario(name, operation):
    try:
        detail=operation();record={'name':name,'status':'passed','detail':detail}
    except Exception as error:
        record={'name':name,'status':'failed','error':str(error)}
    results.append(record);print(json.dumps(record),flush=True)


def guard():
    before=state()['owner_value']
    command(['/usr/bin/python3','-I','/usr/lib/orez/owner_setup.py'],expected=1)
    assert before==state()['owner_value'] and not READY.exists()
    return 'Production CLI refuses this non-live host before changing an account.'


def cancelled():
    for name,answers in [('cancel',[b'\x03']),('short',[b'short\n']),
                         ('mismatch',[SECRET.encode()+b'\n',b'a different dummy phrase\n'])]:
        prepare();before=state()['owner_value'];assert console(name,answers)!=0
        assert state()['owner_value']==before and REQUEST.exists() and not READY.exists()
    return 'Cancel, invalid password and mismatch preserve the locked account and enrollment request.'


def successful():
    prepare();assert console('success',[SECRET.encode()+b'\n',SECRET.encode()+b'\n'])==0
    current=state();assert current['root_locked'] and not current['owner_locked']
    assert not REQUEST.exists() and READY.stat().st_mode&0o777==0o600
    assert SECRET not in READY.read_text()
    command(['/usr/bin/python3','-I',str(SCRIPT)])
    return {'local_console_setup':True,'root_locked':True,'completion_idempotent':True,'credential_logged':False}


def sudo_policy():
    user=['runuser','-u',USERNAME,'--']
    command(user+['sudo','-k','-n','/usr/bin/id','-u'],expected=1)
    command(user+['sudo','-k','-S','-p','','/usr/bin/id','-u'],expected=1,input='incorrect fixture password\n')
    result=command(user+['sudo','-k','-S','-p','','/usr/bin/id','-u'],input=SECRET+'\n')
    assert result=='0'
    command(user+['sudo','-n','/usr/bin/id','-u'],expected=1)
    command(['runuser','-u','orez-test','--','sudo','-k','-n','/usr/bin/id','-u'],expected=1)
    command(['runuser','-u','orez-test','--','python3','-I','/usr/lib/orez/owner_setup.py'],expected=1)
    return 'No-password, wrong-password, cached-session and non-admin requests denied; correct owner password permits id -u.'


def hostile_request():
    prepare();before=state()['owner_value']
    REQUEST.unlink();REQUEST.symlink_to('/etc/passwd')
    command(['/usr/bin/python3','-I',str(SCRIPT)],expected=1)
    assert before==state()['owner_value'] and not READY.exists()
    REQUEST.unlink()
    return 'Aliased enrollment request refused before reading a password or changing the account.'


prepare()
for name,fn in [('non-live-production-denial',guard),('cancel-and-mismatch',cancelled),
                ('real-console-password-setup',successful),('effective-sudo-permissions',sudo_policy),
                ('symlink-request-denial',hostile_request)]:scenario(name,fn)
(OUT/'results.json').write_text(json.dumps({'scope':'Real local PAM/password/sudo in disposable rootless container; live-boot guard substituted only in fixture',
 'scenarios':results,'owner_uid':1000,'passwords_or_hashes_recorded':False,
 'polkit_dialog_tested':False,'sddm_login_tested':False,'full_iso_boot_tested':False},indent=2)+'\n')
sys.exit(any(r['status']!='passed' for r in results))
