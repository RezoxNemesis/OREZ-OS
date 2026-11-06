"""Image-build package policy and integrity checks. Never grants host privileges."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

PROTECTED=re.compile(r'^(linux-(image|modules|headers|generic)|grub|shim|casper$|initramfs-tools|sudo$|polkitd$|libpam|systemd|udev$|apt$|dpkg$|openssh-server$|xrdp$)')
BRAVE_SITE='brave-browser-apt-release.s3.brave.com'
UBUNTU_SITES={'archive.ubuntu.com','security.ubuntu.com'}
NAME=re.compile(r'^[a-z0-9][a-z0-9+.-]+$')
DIGEST=re.compile(r'^[0-9a-f]{64}$')


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def installed(text):
    result={}
    for block in text.split('\n\n'):
        fields={line.split(': ',1)[0]:line.split(': ',1)[1] for line in block.splitlines()
                if ': ' in line and not line.startswith((' ','\t'))}
        if fields.get('Status')!='install ok installed':continue
        name=fields.get('Package','');arch=fields.get('Architecture','');version=fields.get('Version','')
        if not NAME.fullmatch(name) or not version or arch not in ['all','amd64','i386']:
            raise ValueError('Unexpected installed-package record')
        key=name+':'+arch
        if key in result:raise ValueError('Duplicate installed-package record')
        result[key]=version
    if not result:raise ValueError('Empty installed-package inventory')
    return result


def profile(path):
    value=json.loads(Path(path).read_text())
    if value.get('schema')!=1 or value.get('release')!='resolute' or value.get('architecture')!='amd64':
        raise ValueError('Unsupported image package profile')
    names=value.get('packages',[])
    if not isinstance(names,list) or not names or len(names)!=len(set(names)) or any(not isinstance(x,str) or not NAME.fullmatch(x) for x in names):
        raise ValueError('Invalid package names')
    if any(PROTECTED.match(x) for x in names if x not in ['sddm']):
        raise ValueError('Boot/authentication changes need a separate reviewed profile')
    keys=value.get('brave_key_fingerprints',[])
    if not keys or any(not re.fullmatch(r'[A-F0-9]{40}',x) for x in keys):raise ValueError('Invalid Brave key pins')
    budget=value.get('maximum_download_bytes')
    if type(budget)!=int or not 0<budget<=2**30:raise ValueError('Invalid download budget')
    return value


def key_fingerprints(colons):
    keys=[];want=False
    for line in colons.splitlines():
        fields=line.split(':')
        if fields[0]=='pub':want=True
        elif fields[0]=='fpr' and want:
            if len(fields)<=9 or not re.fullmatch(r'[A-F0-9]{40}',fields[9]):raise ValueError('Malformed key fingerprint')
            keys.append(fields[9]);want=False
        elif fields[0]=='sub':want=False
    return set(keys)


def validate_change(change):
    name=change['name'];url=urlsplit(change['uri'])
    if not NAME.fullmatch(name) or change['architecture'] not in ['amd64','all']:
        raise ValueError('Unexpected package or architecture')
    if change['operation'] not in ['install','upgrade'] or PROTECTED.match(name):
        raise ValueError('Removal, downgrade or protected package change refused: '+name)
    if change['trusted'] is not True or not DIGEST.fullmatch(change['sha256']):
        raise ValueError('Untrusted package metadata: '+name)
    if url.scheme!='https' or url.username or url.password or url.port not in [None,443] or url.query or url.fragment:
        raise ValueError('Unexpected package download URI')
    if url.hostname not in UBUNTU_SITES and not (url.hostname==BRAVE_SITE and name in ['brave-browser','brave-keyring']):
        raise ValueError('Repository is not authorized for this package: '+name)
    if type(change['bytes'])!=int or change['bytes']<=0:raise ValueError('Invalid package size')
    filename=change['file']
    if not isinstance(filename,str) or Path(filename).name!=filename or not filename.endswith('.deb') or '\\' in filename:
        raise ValueError('Unsafe package filename')


def verify_bundle(folder):
    folder=Path(folder)
    manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('schema')!=1 or manifest.get('purpose')!='orez-image-app-packages' or manifest.get('installation_approved') is not False:
        raise ValueError('Not a reviewed application package bundle')
    files=set()
    for change in manifest['changes']:
        validate_change(change)
        if change['file'] in files:raise ValueError('Duplicate package file')
        files.add(change['file']);path=folder/'debs'/change['file']
        if path.is_symlink() or not path.is_file() or path.stat().st_size!=change['bytes'] or sha(path)!=change['sha256']:
            raise ValueError('Package integrity mismatch: '+change['name'])
    if files!={p.name for p in (folder/'debs').iterdir()}:
        raise ValueError('Unrecorded package payload')
    return manifest


def verify_transition(before,after,changes):
    expected=dict(before)
    for change in changes:
        validate_change(change)
        key=change['name']+':'+change['architecture']
        if before.get(key)!=change['previous_version']:raise ValueError('Plan does not match original package state')
        expected[key]=change['version']
    if after!=expected:
        raise ValueError('Installed package state differs from the exact reviewed transaction')
