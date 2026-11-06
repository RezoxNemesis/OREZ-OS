"""Upgrade the previous actual OREZ artifact in an isolated, offline container."""
import hashlib,json,os
from pathlib import Path
import subprocess

assert os.getuid()==0 and Path('/.dockerenv').exists() and os.environ.get('OREZ_DISPOSABLE_TEST')=='1'
E=Path('/evidence'); results=[]

def run(args,expected=0):
 p=subprocess.run(args,text=True,capture_output=True,timeout=90)
 with (E/'native-upgrade.log').open('a') as f:f.write(repr(args)+'\n'+p.stdout+p.stderr+'\n')
 assert p.returncode==expected,(args,p.returncode,p.stderr[-1200:])
 return p.stdout.strip()

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def record(name,detail):
 results.append({'name':name,'status':'passed','detail':detail});print(json.dumps(results[-1]),flush=True)

old=run(['dpkg-deb','--field','/input/previous.deb','Version'])
new=run(['dpkg-deb','--field','/input/orez-shell.deb','Version'])
run(['dpkg','--compare-versions',old,'lt',new])
apt=['apt-get','-y','--no-install-recommends','-o','Dpkg::Options::=--path-include=/usr/share/doc/orez/*']
user=['runuser','-u','orez-test','--','env','HOME=/home/orez-test']
try:
 run(apt+['install','/input/previous.deb'])
 assert run(['dpkg-query','-W','-f=${Version}','orez-shell'])==old
 old_command=digest('/usr/bin/orezctl')
 record('previous verified artifact installed',{'version':old,'sha256':digest('/input/previous.deb')})
 run(user+['orezctl','appearance','disable'])
 fixture='''from pathlib import Path
import json
home=Path.home(); (home/'QA project').mkdir()
(home/'QA project'/'日本語.txt').write_text('Owner project survives an OREZ component upgrade.\\n')
root=home/'.local/share/orez/android';root.mkdir(parents=True,mode=0o700)
(root/'config.json').write_text(json.dumps({'memory_mb':2048,'cores':2,'graphics':'software'}));(root/'config.json').chmod(0o600)
'''
 run(user+['python3','-c',fixture])
 paths=['/home/orez-test/QA project/日本語.txt','/home/orez-test/.config/autostart/orez-initialize.desktop','/home/orez-test/.local/share/orez/android/config.json']
 before={p:digest(p) for p in paths}
 record('user state prepared',{'paths':paths,'android_configuration_mode':'0600','credentials':'none; fixture data only'})
 denied=subprocess.run(user+['dpkg','-i','/input/orez-shell.deb'],capture_output=True,text=True)
 (E/'non-admin-upgrade-denial.txt').write_text(denied.stdout+denied.stderr)
 assert 'superuser' in denied.stderr.lower(),denied.stderr
 assert denied.returncode!=0 and run(['dpkg-query','-W','-f=${Version}','orez-shell'])==old
 record('ordinary-user upgrade denied',{'exit_code':denied.returncode,'version_unchanged':True})
 run(apt+['install','/input/orez-shell.deb'])
 assert run(['dpkg-query','-W','-f=${Version}','orez-shell'])==new
 assert digest('/usr/bin/orezctl')!=old_command,'Expected changed native command did not update'
 assert run(user+['orezctl','version'])=='OREZ native components: '+new
 assert before=={p:digest(p) for p in paths}
 assert Path(paths[2]).stat().st_mode&0o777==0o600
 assert not run(['dpkg','--audit'])
 record('actual revision upgraded with state intact',{'from':old,'to':new,'changed_command_verified':True,'user_files_preferences_android_settings_unchanged':True})
 run(apt+['install','/input/orez-shell.deb'])
 assert before=={p:digest(p) for p in paths}
 record('repeat installation stable',{'version':new,'user_state_preserved':True})
finally:
 (E/'native-upgrade-results.json').write_text(json.dumps({'installation_approved':False,'signed_repository_tested':False,'scenarios':results},indent=2)+'\n')
