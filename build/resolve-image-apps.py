#!/usr/bin/env python3
"""Resolve/download a signed package closure for a base status snapshot; no install.

Use in the image-tools environment. The output is a fresh isolated APT root,
authenticated indexes, exact plan and package hashes. Never calls cache.commit,
dpkg installation, a shell, or any privileged service on the workstation.
"""
import argparse
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
from image_packages import BRAVE_SITE, installed, key_fingerprints, profile, sha, validate_change, verify_bundle


def regular(path):
    if path.is_symlink() or not path.is_file():raise ValueError('Input must be a regular unaliased file: '+str(path))
    return path


def resolve(args):
    # Build metadata and packages contain no credentials. Explicit public-read
    # staging lets APT retain its _apt download sandbox under restrictive umasks.
    os.umask(0o022)
    value=profile(args.profile)
    for path in [args.status,args.ubuntu_keyring,args.brave_keyring]:regular(path)
    before=installed(args.status.read_text())
    keys=subprocess.check_output(['gpg','--batch','--show-keys','--with-colons',str(args.brave_keyring)],text=True)
    if key_fingerprints(keys)!=set(value['brave_key_fingerprints']):raise ValueError('Brave signing keys changed; review before use')
    output=args.output.absolute()
    if any(p.is_symlink() for p in [output,*output.parents]) or any(c in str(output) for c in ['"','\n','\r','\\']):
        raise ValueError('Unsafe output path')
    output.mkdir(mode=0o755,parents=False,exist_ok=False)
    root=output/'apt-root';debs=output/'debs';debs.mkdir(mode=0o755)
    downloads=output/'download-partial';downloads.mkdir(mode=0o700)
    if os.geteuid()==0:os.chown(downloads,pwd.getpwnam('_apt').pw_uid,0)
    for name in ['etc/apt/apt.conf.d','etc/apt/sources.list.d','etc/apt/preferences.d','etc/apt/trusted.gpg.d','var/lib/dpkg','usr/share/keyrings']:
        (root/name).mkdir(parents=True,mode=0o755,exist_ok=True)
    for source,target in [(args.status,'var/lib/dpkg/status'),(args.ubuntu_keyring,'usr/share/keyrings/ubuntu.gpg'),(args.brave_keyring,'usr/share/keyrings/brave.gpg')]:
        shutil.copyfile(source,root/target);(root/target).chmod(0o644)
    lines=[]
    for uri,suites,key in [('https://archive.ubuntu.com/ubuntu/','resolute resolute-updates','ubuntu.gpg'),('https://security.ubuntu.com/ubuntu/','resolute-security','ubuntu.gpg'),('https://'+BRAVE_SITE+'/','stable','brave.gpg')]:
        components='main' if key=='brave.gpg' else 'main restricted universe multiverse'
        lines.append(f'Types: deb\nURIs: {uri}\nSuites: {suites}\nComponents: {components}\nArchitectures: amd64\nSigned-By: {root}/usr/share/keyrings/{key}\n')
    (root/'etc/apt/sources.list.d/orez-build.sources').write_text('\n'.join(lines))
    (root/'etc/apt/preferences.d/brave-scope').write_text(
        'Package: brave-browser brave-keyring\nPin: origin "'+BRAVE_SITE+'"\nPin-Priority: 500\n\n'
        'Package: *\nPin: origin "'+BRAVE_SITE+'"\nPin-Priority: -1\n')
    config=f'''Dir "{root}";
Dir::State::status "{root}/var/lib/dpkg/status";
Dir::Etc::trusted "/dev/null";
APT::Architecture "amd64";
APT::Architectures {{ "amd64"; }};
APT::Install-Recommends "false";
APT::Install-Suggests "false";
APT::Get::AllowUnauthenticated "false";
Acquire::AllowInsecureRepositories "false";
Acquire::AllowDowngradeToInsecureRepositories "false";
APT::Update::Error-Mode "any";
'''
    if args.ca_file:
        regular(args.ca_file)
        if any(c in str(args.ca_file) for c in ['"','\n','\r','\\']):raise ValueError('Unsafe CA path')
        config+=f'Acquire::https::CaInfo "{args.ca_file.absolute()}";\n'
    config_path=root/'etc/apt/apt.conf';config_path.write_text(config)
    os.environ['APT_CONFIG']=str(config_path)
    import apt
    import apt_pkg
    apt_pkg.config.clear('');apt_pkg.init_config()
    cache=apt.Cache(rootdir=str(root))
    if os.geteuid()==0:
        for path in [config_path,root/'etc/apt/sources.list.d/orez-build.sources',root/'usr/share/keyrings/ubuntu.gpg',root/'usr/share/keyrings/brave.gpg']:
            if subprocess.run(['runuser','-u','_apt','--','test','-r',str(path)]).returncode:
                raise ValueError('APT sandbox cannot traverse staging; use an accessible build directory')
    cache.update();cache.open()
    # Keep existing base versions unless a dependency requires a change. This
    # application stage is not an unattended full distribution upgrade.
    for name in value['packages']:
        if name not in cache:raise ValueError('Required package unavailable: '+name)
        if not cache[name].is_installed:cache[name].mark_install(auto_fix=True,auto_inst=True,from_user=True)
    if cache.broken_count:raise ValueError('Unresolved application dependencies')
    changes=[]
    for pkg in sorted(cache.get_changes(),key=lambda p:p.name):
        ver=pkg.candidate
        operation='remove' if pkg.marked_delete else 'downgrade' if pkg.marked_downgrade else 'upgrade' if pkg.is_installed else 'install'
        change={'name':pkg.name,'version':ver.version,'previous_version':pkg.installed.version if pkg.is_installed else None,
                'architecture':ver.architecture,'operation':operation,'uri':ver.uri,'sha256':ver.record.get('SHA256',''),
                'bytes':ver.size,'trusted':any(o.trusted for o in ver.origins),'file':Path(ver.filename).name}
        validate_change(change);changes.append(change)
    if sum(c['bytes'] for c in changes)>value['maximum_download_bytes']:raise ValueError('Package plan exceeds reviewed download budget')
    plan={'schema':1,'purpose':'orez-image-app-packages','base_status_sha256':sha(args.status),'profile_sha256':sha(args.profile),
          'profile':value,'base_inventory':before,'changes':changes,'installation_approved':False,'installed':False,
          'trust_note':'APT authenticates repository metadata and payload hashes; it cannot prove absence of malicious publisher code.'}
    (output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({'base_packages':len(before),'changes':len(changes),'download_bytes':sum(c['bytes'] for c in changes),
                      'transaction':[{k:c[k] for k in ['name','version','operation']} for c in changes]},indent=2),flush=True)
    for change in changes:
        path=Path(cache[change['name']].candidate.fetch_binary(str(downloads),allow_unauthenticated=False))
        if path.parent!=downloads or path.name!=change['file'] or path.is_symlink():raise ValueError('Unexpected fetched package path')
        if os.geteuid()==0:os.chown(path,0,0)
        path.chmod(0o644)
        if path.stat().st_size!=change['bytes'] or sha(path)!=change['sha256']:raise ValueError('Fetched package differs from authenticated metadata')
        path.rename(debs/path.name)
    downloads.rmdir()
    plan['repository_indexes']={p.name:sha(p) for p in (root/'var/lib/apt/lists').iterdir() if p.is_file() and p.name!='lock'}
    (output/'manifest.json').write_text(json.dumps(plan,indent=2)+'\n')
    verify_bundle(output)
    print('PASS: signed repository dependency closure downloaded and SHA-256 verified; no packages installed.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['status','ubuntu-keyring','brave-keyring','profile','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--ca-file',type=Path)
    try:resolve(p.parse_args())
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        print('Image package resolution refused: '+str(error),file=sys.stderr);sys.exit(1)
