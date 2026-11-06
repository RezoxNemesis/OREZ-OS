#!/usr/bin/env python3
"""Install the script-free OREZ package in an offline staging root and pack its delta.

The original SquashFS and app layer remain lower layers. Never ship this temporary
root, which lacks runtime devices and original xattrs. No installer is enabled.
"""
import argparse,importlib.util,json,os,shutil,socket,stat,subprocess
from pathlib import Path,PurePosixPath
from app_layer import inventory
from image_packages import installed,sha
from live_assembly import verify_base

def load(name):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
staging=load('stage-image-root');installer=load('install-image-apps');packer=load('pack-app-layer')
REPO=Path(__file__).resolve().parents[1]

def allowed_changes(before,after,payload):
 if set(before)-set(after):raise ValueError('OREZ delta cannot represent deleted paths')
 changed={k:v for k,v in after.items() if before.get(k)!=v}
 ancestors={str(p) for name in payload for p in PurePosixPath(name).parents if str(p)!='.'}
 for name,item in changed.items():
  permitted=name in payload or (item['type']=='directory' and name in ancestors) or name.startswith('var/lib/dpkg/') or name in ['var/lib/dpkg','usr/share/applications/mimeinfo.cache','var/lib/apt/extended_states']
  if not permitted:raise ValueError('Unreviewed component transaction path: '+name)
  if name in before and before[name]['type']!=item['type']:raise ValueError('Inode type changed: '+name)
  if item['mode']&0o6000 or item.get('xattrs'):raise ValueError('Unexpected privilege/attribute change: '+name)
 return changed

def main(a):
 os.umask(0o022);staging.require_build_container()
 if any(n!='lo' for _,n in socket.if_nameindex()):raise ValueError('Component staging requires offline networking')
 root=staging.work_path(a.root);out=staging.work_path(a.output);out.mkdir(exist_ok=False)
 profile=json.loads((REPO/'image/live-assembly.json').read_text())
 if sha(root/'var/lib/dpkg/status')!=profile['app_status_sha256']:raise ValueError('Root is not the reviewed application state')
 marker=json.loads(root.with_suffix('.orez-build.json').read_text())
 if marker['input_iso_sha256'] not in [profile['development_parent_sha256'],profile['official_iso_sha256']]:raise ValueError('Wrong staging parent')
 offset,_=verify_base(a.iso,marker['input_iso_sha256']==profile['development_parent_sha256'])
 if marker['offset']!=offset:raise ValueError('Staging offset differs from the verified parent')
 payload={line for raw in (REPO/'image/installer/installed-files.txt').read_text().splitlines() if (line:=raw.strip()) and not line.startswith('#')}
 control=out/'control';subprocess.run(['dpkg-deb','-e',str(a.package),str(control)],check=True)
 if {p.name for p in control.iterdir()}!={'control'}:raise ValueError('OREZ must remain free of maintainer scripts/triggers')
 version=subprocess.check_output(['python3',str(REPO/'build/package-info.py'),'version'],text=True).strip()
 subprocess.run(['python3',str(REPO/'build/verify-deb-files.py'),'--package',str(a.package),'--version',version,'--manifest',str(REPO/'image/installer/installed-files.txt'),'--report',str(out/'package-audit.json')],check=True)
 # Bind the package to current source bytes, not only an arbitrary .deb label.
 extracted=out/'package-data';subprocess.run(['dpkg-deb','-x',str(a.package),str(extracted)],check=True)
 for name in payload:
  if (extracted/name).is_symlink() or (extracted/name).read_bytes()!=(REPO/'overlay'/name).read_bytes():raise ValueError('Package/source differs: '+name)
 before=inventory(root);(out/'before.json').write_text(json.dumps(before,separators=(',',':'))+'\n')
 baseline=installed((root/'var/lib/dpkg/status').read_text());log=out/'install.log'
 null=(root/'dev/null').stat()
 if not stat.S_ISCHR(null.st_mode) or null.st_rdev!=os.makedev(1,3):raise ValueError('Container null device required')
 package=root/'run/orez-component.deb';shutil.copyfile(a.package,package)
 try:
  if installer.run(root,['/usr/bin/dpkg','--audit'],log).strip():raise ValueError('Incomplete base package state')
  installer.run(root,['/usr/bin/dpkg','--install','/run/orez-component.deb'],log)
  if installer.run(root,['/usr/bin/dpkg','--audit'],log).strip():raise ValueError('Incomplete component transaction')
  installer.run(root,['/usr/bin/apt-mark','manual','orez-shell'],log)
 finally:package.unlink(missing_ok=True)
 final=installed((root/'var/lib/dpkg/status').read_text())
 if final!={**baseline,'orez-shell:all':version}:raise ValueError('Unexpected package transition')
 after=inventory(root);(out/'after.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
 changed=allowed_changes(before,after,payload);required=set(changed)
 for name in changed:required.update(str(p) for p in PurePosixPath(name).parents if str(p)!='.')
 original=packer.original_xattrs(a.iso,marker['offset'])
 if set(original)&required:raise ValueError('Delta would shadow omitted original attributes')
 layer=out/'layer';layer.mkdir()
 for name in sorted(required,key=lambda n:(len(PurePosixPath(n).parts),n)):
  src=root/name;dst=layer/name;item=after[name]
  if item['type']=='directory':dst.mkdir(exist_ok=True);os.chown(dst,item['uid'],item['gid']);shutil.copystat(src,dst)
  elif item['type']=='link':dst.symlink_to(item['target']);os.lchown(dst,item['uid'],item['gid'])
  else:os.link(src,dst)
 expected={name:after[name] for name in required}
 if inventory(layer)!=expected:raise ValueError('Delta does not match installed metadata')
 image=out/'orez-install.squashfs'
 subprocess.run(['mksquashfs',str(layer),str(image),'-noappend','-no-progress','-processors','2','-mem','128M','-comp','xz','-all-time','1793923200','-mkfs-time','1793923200'],check=True)
 roundtrip=out/'roundtrip';subprocess.run(['unsquashfs','-no-progress','-processors','2','-d',str(roundtrip),str(image)],check=True)
 if inventory(roundtrip)!=expected:raise ValueError('Packed OREZ layer differs from the actual installation')
 status=roundtrip/'var/lib/dpkg/status';ownership=roundtrip/'var/lib/dpkg/info/orez-shell.list'
 if not ownership.is_file() or not payload<={line.lstrip('/') for line in ownership.read_text().splitlines()}:raise ValueError('dpkg ownership missing')
 result={'schema':1,'purpose':'orez-dpkg-owned-components','version':version,'package_sha256':sha(a.package),'application_status_sha256':profile['app_status_sha256'],'installed_status_sha256':sha(status),'layer_sha256':sha(image),'layer_bytes':image.stat().st_size,'changed_paths':sorted(changed),'verified_paths':len(expected),'package_count':len(final),'source_profile_sha256':sha(REPO/'image/live-assembly.json'),'full_iso_built':False,'boot_tested':False,'installation_approved':False}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for key in ['root','output','package','iso']:p.add_argument('--'+key,type=Path,required=True)
 main(p.parse_args())
