#!/usr/bin/env python3
"""Unprivileged OREZ Store for native apps and actual Android app integration.

Android consumer installation remains unqualified. No web-app substitution,
APK mirror, purchase automation, root helper or system configuration change.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit

CATALOG=Path('/usr/share/orez/store-catalog.json')
NATIVE={'brave-linux':['/usr/bin/brave-browser','/usr/bin/brave-browser-stable'],
        'chrome-linux':['/usr/bin/google-chrome','/usr/bin/google-chrome-stable'],
        'vlc':['/usr/bin/vlc'],'supertux':['/usr/games/supertux2','/usr/bin/supertux2']}


def normal_user():
    if os.getuid()==0 or os.geteuid()==0:
        raise ValueError('Open OREZ Store as your ordinary desktop user, never administrator/root.')


def safe_path(path):
    for item in [path,*path.parents]:
        if item.is_symlink():raise ValueError('Store storage must not contain symlinks.')


def read_catalog(path=CATALOG):
    value=json.loads(Path(path).read_text())
    if not isinstance(value,dict) or value.get('schema_version')!=1 or not isinstance(value.get('apps'),list):
        raise ValueError('Unsupported Store catalog.')
    result={}
    for app in value['apps']:
        if not isinstance(app,dict) or set(app)!={'id','name','kind','category','publisher','summary','url','compatibility','privacy'}:
            raise ValueError('Unrecognized catalog fields.')
        if any(not isinstance(v,str) or not v or any(ord(c)<32 for c in v) for v in app.values()):
            raise ValueError('Invalid catalog text.')
        key=app['id'];url=urlsplit(app['url'])
        if not re.fullmatch('[a-z][a-z0-9-]{1,40}',key) or key in result:raise ValueError('Invalid or duplicate app ID.')
        if url.scheme!='https' or not url.hostname or url.username or url.password or url.port or url.fragment:
            raise ValueError('Catalog links must use ordinary HTTPS URLs.')
        if app['kind'] not in ['native','android']:raise ValueError('Only native Linux and actual Android apps are offered.')
        result[key]=app
    return result


class Store:
    def __init__(self,root=None,catalog=CATALOG):
        data=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
        self.root=Path(root) if root else data/'orez/store'
        if not self.root.is_absolute():raise ValueError('Store path must be absolute.')
        self.apps=read_catalog(catalog)
    def app(self,key):
        if key not in self.apps:raise ValueError('Unknown app; arbitrary commands and URLs are not accepted.')
        return self.apps[key]
    def prepare(self):
        normal_user();safe_path(self.root);self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        if self.root.stat().st_uid!=os.getuid():raise ValueError('Store data must belong to this user.')
        marker=self.root/'.orez-store'
        if marker.is_symlink():raise ValueError('Aliased storage marker.')
        if not marker.exists():
            if any(self.root.iterdir()):raise ValueError('Unrecognized Store data is not adopted.')
            with marker.open('x') as stream:stream.write('OREZ Store v1\n')
            marker.chmod(0o600)
        if marker.read_text()!='OREZ Store v1\n':raise ValueError('Unknown Store storage version.')
        self.root.chmod(0o700)
    def audit(self,action,key):
        self.prepare();fd=os.open(self.root/'actions.jsonl',os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'a') as stream:
            stream.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':action,'app':key})+'\n')
    def executable(self,key):
        return next((p for p in NATIVE.get(key,[]) if Path(p).is_file() and os.access(p,os.X_OK)),None)
    def status(self,key):
        normal_user();app=self.app(key)
        if app['kind']=='native':
            installed=bool(self.executable(key))
            return {'installed':installed,'state':'Native app detected' if installed else 'Official installation required',
                    'administrator_access_granted':False,'filesystem_isolated':False}
        return {'installed':False,'state':'Android runtime pending','administrator_access_granted':False,
                'compatibility_verified':False,'consumer_provider_qualified':False,'web_fallback':False}
    def launch_plan(self,key):
        normal_user();app=self.app(key)
        if app['kind']=='android':raise ValueError('Android consumer runtime is not qualified. This app will not be replaced with a website.')
        binary=self.executable(key)
        if not binary:raise ValueError('Native app is not installed. Review its official installation source.')
        return [binary]
    def launch(self,key):
        plan=self.launch_plan(key);self.prepare()
        fd=os.open(self.root/('launch-'+key+'.log'),os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'ab') as log:subprocess.Popen(plan,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        self.audit('native-launch-requested',key)
    def runtime_controls(self,confirmed=False):
        normal_user()
        if not confirmed:raise ValueError('Opening the development runtime controls requires confirmation.')
        self.prepare();subprocess.Popen(['/usr/bin/orez-android','gui'],stdin=subprocess.DEVNULL,start_new_session=True)
        self.audit('development-runtime-controls-requested','android')
    def open_source(self,key,confirmed=False):
        normal_user();app=self.app(key)
        if not confirmed:raise ValueError('Opening an informational website requires confirmation.')
        self.prepare();subprocess.Popen(['/usr/bin/xdg-open',app['url']],stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        self.audit('official-information-requested',key)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['gui','list','status','launch','source','runtime'],nargs='?',default='gui')
    parser.add_argument('app',nargs='?');parser.add_argument('--confirm',action='store_true');args=parser.parse_args()
    try:
        normal_user();store=Store()
        if args.action=='gui':
            from store_ui import run
            return run(store)
        if args.action=='list':print(json.dumps(list(store.apps.values()),indent=2));return 0
        if args.action=='runtime':store.runtime_controls(args.confirm);return 0
        if not args.app:parser.error('an app ID is required')
        if args.action=='status':print(json.dumps(store.status(args.app),indent=2))
        elif args.action=='launch':store.launch(args.app)
        elif args.action=='source':store.open_source(args.app,args.confirm)
        return 0
    except ImportError:
        print('Native Store GUI requires python3-pyside6.qtwidgets. Install the declared package dependencies; CLI list/status remain available.',file=sys.stderr);return 2
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        print('OREZ Store: '+str(error),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
