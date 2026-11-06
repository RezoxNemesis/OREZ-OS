"""Exact additive filesystem delta. Reject deletions and sensitive policy changes."""
import base64
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import stat
from image_packages import sha

IGNORED=('dev','proc','sys','run','tmp','var/log','var/cache/apt')
PROTECTED=('boot','usr/lib/modules','etc/passwd','etc/shadow','etc/group','etc/gshadow',
           'etc/sudoers','etc/sudoers.d','etc/pam.d','etc/polkit-1','usr/share/polkit-1',
           'usr/lib/systemd','etc/systemd','etc/ssh','etc/grub.d','etc/security',
           'etc/ld.so.preload','var/spool/cron','etc/cron.d','etc/cron.hourly',
           'etc/cron.weekly','etc/cron.monthly','root','home','etc/xdg/autostart')


def under(path,prefixes):return any(path==x or path.startswith(x+'/') for x in prefixes)


def inventory(root):
    root=Path(root);result={}
    for directory,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[x for x in dirs if not under(str((Path(directory)/x).relative_to(root)),IGNORED)]
        for path in [Path(directory)/x for x in sorted(dirs+files)]:
            name=str(path.relative_to(root))
            if under(name,IGNORED):continue
            info=path.lstat();item={'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid}
            if stat.S_ISLNK(info.st_mode):item.update(type='link',target=os.readlink(path))
            elif stat.S_ISDIR(info.st_mode):item['type']='directory'
            elif stat.S_ISREG(info.st_mode):item.update(type='file',bytes=info.st_size,sha256=sha(path))
            else:raise ValueError('Unexpected non-runtime special file: '+name)
            item['xattrs']={key:base64.b64encode(os.getxattr(path,key,follow_symlinks=False)).decode() for key in sorted(os.listxattr(path,follow_symlinks=False))}
            result[name]=item
    return result


def delta(before,after):
    removed=sorted(set(before)-set(after))
    if removed:raise ValueError('Additive layer cannot represent deletions: '+', '.join(removed[:8]))
    changed={name:value for name,value in after.items() if before.get(name)!=value}
    for name,value in changed.items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path)!=name:raise ValueError('Unsafe layer path')
        if under(name,PROTECTED):raise ValueError('Application installation changed protected system policy: '+name)
        if name.startswith('etc/cron.daily/') and name!='etc/cron.daily/brave-browser':
            raise ValueError('Unreviewed scheduled job: '+name)
        if name in before and before[name]['type']!=value['type']:raise ValueError('Layer cannot safely change inode type: '+name)
        if value['mode']&0o6000:
            if (name!='opt/brave.com/brave/chrome-sandbox' or value['type']!='file' or
                value['mode']!=0o4755 or value['uid']!=0 or value['gid']!=0):
                raise ValueError('Unreviewed new setuid/setgid path: '+name)
        if 'security.capability' in value.get('xattrs',{}):
            raise ValueError('New or changed file capabilities require separate review: '+name)
    return changed


def stage_delta(root,output,before,after):
    changed=delta(before,after);output=Path(output);root=Path(root)
    output.mkdir(mode=0o755,exist_ok=False)
    required=set(changed)
    for name in changed:
        required.update(str(p) for p in PurePosixPath(name).parents if str(p)!='.')
    for name in sorted(required,key=lambda x:(len(PurePosixPath(x).parts),x)):
        item=after[name];source=root/name;target=output/name
        if item['type']=='directory':target.mkdir(exist_ok=True)
        elif item['type']=='link':target.symlink_to(item['target'])
        else:os.link(source,target,follow_symlinks=False)
        if item['type']=='directory':
            os.chown(target,item['uid'],item['gid']);shutil.copystat(source,target,follow_symlinks=False)
        elif item['type']=='link':os.lchown(target,item['uid'],item['gid'])
    actual=inventory(output)
    expected={name:after[name] for name in required}
    if actual!=expected:raise ValueError('Staged layer metadata/bytes differ from the installed root')
    return {'changed_paths':len(changed),'layer_paths_with_ancestors':len(required),'removed_paths':[],
            'protected_policy_changes':[],'setid_paths':[p for p,v in changed.items() if v['mode']&0o6000],
            'cron_paths':[p for p in changed if p.startswith('etc/cron')],
            'new_or_changed_files':{k:v for k,v in changed.items() if v['type']!='directory'},
            'installation_approved':False,'runtime_xattrs_omitted_only_in_temporary_base':True}
