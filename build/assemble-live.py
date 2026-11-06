#!/usr/bin/env python3
"""Compose verified base/app/dpkg-owned OREZ/owner layers into a blocked live ISO.

No disk devices or host installation. Development-parent mode reuses a recorded
old local ISO; it is NOT a fresh authenticated canonical build or release.
"""
import argparse,importlib.util,json,os,shutil,subprocess,tempfile
from pathlib import Path
from image_packages import installed,sha
from live_assembly import ROOT,profile,verify_base,verify_components,brand_grub,extent,digest_range

def module(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'build'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
media=module('update-media-checksums');patch=module('patch-live-initrd')

def extract(iso,name,dest):
 subprocess.run(['xorriso','-osirrox','on','-indev',str(iso),'-extract',name,str(dest)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def assemble(a):
 os.umask(0o022)
 if a.output.exists() or a.output.is_symlink():raise ValueError('Require a new output ISO')
 a.output.parent.mkdir(parents=True,exist_ok=True)
 if shutil.disk_usage(a.output.parent).free<a.iso.stat().st_size+a.apps.stat().st_size+700*1024**2:raise ValueError('Insufficient complete output/scratch space')
 offset,size=verify_base(a.iso,a.development_parent)
 status,version=verify_components(a.apps,a.components,a.component_report)
 with tempfile.TemporaryDirectory(prefix='orez-compose-',dir=a.output.parent) as temporary:
  work=Path(temporary);old=work/'initrd-original';extract(a.iso,'/casper/initrd',old)
  patch.patch(old,work/'initrd',work/'orez-initrd.json',owner_setup=True)
  subprocess.run(['python3',str(ROOT/'build/stage-overlay.py'),'--source',str(ROOT/'overlay'),'--output',str(work/'live'),'--live-owner'],check=True)
  subprocess.run(['mksquashfs',str(work/'live'),str(work/'zz-orez.squashfs'),'-noappend','-no-progress','-processors','2','-mem','128M','-comp','xz','-all-root','-all-time','1793923200','-mkfs-time','1793923200'],check=True)
  subprocess.run(['python3',str(ROOT/'build/verify-live-owner.py'),'--source',str(ROOT/'image/live-owner'),'--squashfs',str(work/'zz-orez.squashfs')],check=True)
  extract(a.iso,'/boot/grub/grub.cfg',work/'grub-original.cfg');(work/'grub.cfg').write_text(brand_grub((work/'grub-original.cfg').read_text()))
  # The owner-only session is a live test. It never offers automatic install.
  (work/'info').write_text('OREZ OS 0.1 development amd64 — Kubuntu 26.04.1 base — installation disabled\n')
  packages=installed(status.decode());(work/'filesystem.manifest').write_text(''.join(name.split(':')[0]+' '+version+'\n' for name,version in sorted(packages.items())))
  # Sum filesystem uncompressed upper bounds for diagnostics; not an installed footprint.
  report={'schema':1,'parent_kind':'recorded-development-derivative' if a.development_parent else 'pinned-official-image','parent_sha256':sha(a.iso),'base_filesystem_sha256':profile()['base_filesystem_sha256'],'application_layer_sha256':sha(a.apps),'component_layer_sha256':sha(a.components),'component_package_version':version,'package_count':len(packages),'layers_low_to_high':profile()['layer_order_low_to_high'],'source_commit':os.environ.get('OREZ_SOURCE_COMMIT','working-tree'),'fresh_signature_check_by_this_script':False,'boot_tested':False,'installation_approved':False,'release_approved':False}
  (work/'orez-assembly.json').write_text(json.dumps(report,indent=2)+'\n')
  mapped={'/casper/initrd':work/'initrd','/casper/orez-initrd.json':work/'orez-initrd.json','/casper/zz-orez.squashfs':work/'zz-orez.squashfs','/casper/orez-install.squashfs':a.components,'/casper/orez-apps.squashfs':a.apps,'/casper/orez-assembly.json':work/'orez-assembly.json','/casper/filesystem.manifest':work/'filesystem.manifest','/boot/grub/grub.cfg':work/'grub.cfg','/.disk/info':work/'info'}
  extract(a.iso,'/md5sum.txt',work/'old-md5sum.txt');entries=media.parse((work/'old-md5sum.txt').read_text());entries.update({'.'+name:media.md5(path) for name,path in mapped.items()})
  (work/'md5sum.txt').write_text(''.join(digest+'  '+name+'\n' for name,digest in entries.items()));mapped['/md5sum.txt']=work/'md5sum.txt'
  command=['xorriso','-indev',str(a.iso),'-outdev',str(a.output)]
  for name,path in mapped.items():command+=['-map',str(path),name]
  command+=['-boot_image','any','replay','-commit']
  with a.output.with_suffix('.build.log').open('w') as log:subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
  # Compare every changed media file extracted from the finished image.
  for i,(name,path) in enumerate(mapped.items()):
   checked=work/('checked-'+str(i));extract(a.output,name,checked)
   if sha(checked)!=sha(path):raise ValueError('ISO mapping differs: '+name)
   checked.unlink()
  newoffset,newsize=extent(a.output,'/casper/filesystem.squashfs')
  if newsize!=size or digest_range(a.output,newoffset,newsize)!=profile()['base_filesystem_sha256']:raise ValueError('Original lower filesystem changed')
  report.update(output_sha256=sha(a.output),output_bytes=a.output.stat().st_size,mapped_files_verified=len(mapped),base_filesystem_unchanged=True)
  a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
  a.output.with_suffix('.iso.sha256').write_text(report['output_sha256']+'  '+a.output.name+'\n')
  print(json.dumps(report,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['iso','apps','components','component-report','output']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--development-parent',action='store_true');assemble(p.parse_args())
