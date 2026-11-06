#!/usr/bin/env python3
"""Install exact app closure in an offline disposable root; create additive layer.

The resulting root is temporary staging, NOT a replacement for the original
SquashFS. Original files/devices/xattrs remain in the unchanged lower layer.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
from app_layer import inventory,stage_delta
from image_packages import installed,key_fingerprints,profile,sha,verify_bundle,verify_transition

spec=importlib.util.spec_from_file_location('stage_image_root',Path(__file__).with_name('stage-image-root.py'))
staging=importlib.util.module_from_spec(spec);spec.loader.exec_module(staging)


def run(root,argv,log):
    command=['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/sbin:/usr/bin:/sbin:/bin','HOME=/root',
             'LANG=C.UTF-8','DEBIAN_FRONTEND=noninteractive','SYSTEMD_OFFLINE=1',*argv]
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300)
    with log.open('a') as stream:stream.write(json.dumps(argv)+'\n'+result.stdout+'\n')
    if result.returncode:raise ValueError('Staged command failed; preserve root and log: '+argv[0])
    return result.stdout


def install(args):
    os.umask(0o022)
    staging.require_build_container();root=staging.work_path(args.root);output=staging.work_path(args.output)
    if any(name!='lo' for _,name in socket.if_nameindex()):raise ValueError('Installation requires --network none')
    marker=json.loads(root.with_suffix('.orez-build.json').read_text())
    if marker.get('purpose')!='orez-additive-package-staging' or marker.get('root')!=str(root):raise ValueError('Missing staging identity')
    metadata=verify_bundle(args.bundle);approved=profile(args.profile)
    if metadata['profile_sha256']!=sha(args.profile) or metadata['profile']!=approved:raise ValueError('Package profile changed')
    status=root/'var/lib/dpkg/status'
    if sha(status)!=metadata['base_status_sha256'] or marker['base_status_sha256']!=sha(status):raise ValueError('Stale package plan or altered staging root')
    null=(root/'dev/null').stat()
    if not stat.S_ISCHR(null.st_mode) or null.st_rdev!=os.makedev(1,3):raise ValueError('Staging requires the container null device')
    output.mkdir(mode=0o755,exist_ok=False);log=output/'install.log'
    before=inventory(root);(output/'before.json').write_text(json.dumps(before,separators=(',',':'))+'\n')
    baseline=installed(status.read_text())
    packages=root/'run/orez-image-packages';packages.mkdir(mode=0o755,exist_ok=False)
    policy=root/'usr/sbin/policy-rc.d'
    if policy.is_symlink():raise ValueError('Unexpected policy-rc.d alias')
    saved=(policy.read_bytes(),stat.S_IMODE(policy.stat().st_mode)) if policy.exists() else None
    try:
        paths=[]
        for change in metadata['changes']:
            source=args.bundle/'debs'/change['file']
            fields=subprocess.check_output(['dpkg-deb','-f',str(source),'Package','Version','Architecture'],text=True)
            control=dict(line.split(': ',1) for line in fields.splitlines())
            if control!={'Package':change['name'],'Version':change['version'],'Architecture':change['architecture']}:
                raise ValueError('Actual Debian control identity differs from authenticated plan')
            os.link(source,packages/source.name);paths.append('/run/orez-image-packages/'+source.name)
        policy.write_text('#!/bin/sh\n# OREZ temporary image-build service-start guard.\nexit 101\n');policy.chmod(0o755)
        apt=['/usr/bin/apt-get','--no-download','--no-remove','--no-install-recommends','-o','Dpkg::Use-Pty=0','-y','install',*paths]
        simulation=run(root,[*apt[:1],'--simulate',*apt[1:]],log)
        planned={m.groups() for m in re.finditer(r'^Inst ([^ :]+)(?::\S+)?(?: \[[^\]]+\])? \(([^ ]+)',simulation,re.MULTILINE)}
        if planned!={(x['name'],x['version']) for x in metadata['changes']} or re.search(r'^Remv ',simulation,re.MULTILINE):
            raise ValueError('Offline APT simulation differs from the reviewed transaction')
        # APT's --no-download local-file install can still require a canonical
        # archive-cache filename. After its exact read-only solver check, use
        # dpkg directly: it cannot fetch network content or invent dependencies.
        # No --force options; dependency/configuration failures block the layer.
        if run(root,['/usr/bin/dpkg','--audit'],log).strip():raise ValueError('Base dpkg state is incomplete')
        run(root,['/usr/bin/dpkg','--unpack',*paths],log)
        run(root,['/usr/bin/dpkg','--configure','--pending'],log)
        run(root,['/usr/bin/apt-mark','manual',*approved['packages']],log)
        if run(root,['/usr/bin/dpkg','--audit'],log).strip():raise ValueError('Incomplete dpkg transaction')
        verify_transition(baseline,installed(status.read_text()),metadata['changes'])
        # Scoped update configuration; no vendor repository may replace Ubuntu
        # packages. This is visible to the owner through normal Software Sources.
        keys=root/'usr/share/keyrings/brave-browser-archive-keyring.gpg'
        actual=subprocess.check_output(['gpg','--batch','--show-keys','--with-colons',str(keys)],text=True)
        if key_fingerprints(actual)!=set(approved['brave_key_fingerprints']):raise ValueError('Installed Brave keyring differs from reviewed keys')
        source=root/'etc/apt/sources.list.d/brave-browser-release.sources'
        if source.exists():raise ValueError('Unexpected vendor-created repository: inspect before layer generation')
        source.write_text('Types: deb\nURIs: https://brave-browser-apt-release.s3.brave.com/\nSuites: stable\nComponents: main\nArchitectures: amd64\nSigned-By: /usr/share/keyrings/brave-browser-archive-keyring.gpg\n');source.chmod(0o644)
        pin=root/'etc/apt/preferences.d/orez-brave-scope'
        if pin.exists():raise ValueError('Unexpected existing vendor scope policy')
        pin.write_text((args.bundle/'apt-root/etc/apt/preferences.d/brave-scope').read_text());pin.chmod(0o644)
    finally:
        shutil.rmtree(packages)
        if saved:policy.write_bytes(saved[0]);policy.chmod(saved[1])
        else:policy.unlink(missing_ok=True)
    after=inventory(root)
    report=stage_delta(root,output/'layer',before,after)
    report.update(schema=1,base_status_sha256=metadata['base_status_sha256'],installed_status_sha256=sha(status),
                  package_changes=metadata['changes'],profile_sha256=sha(args.profile),
                  source_iso_sha256=marker['input_iso_sha256'],native_apps_launched=False,full_iso_built=False)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'after.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['new_or_changed_files','package_changes']},indent=2))
    print('PASS: offline packages registered, exact transaction preserved, additive layer staged. Not boot/installer approval.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['root','bundle','profile','output']:p.add_argument('--'+name,type=Path,required=True)
    install(p.parse_args())
