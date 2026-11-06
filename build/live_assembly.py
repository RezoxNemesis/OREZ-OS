"""Exact input identities and casper overlay semantics for the reviewed live base."""
import hashlib,json,re,subprocess
from pathlib import Path,PurePosixPath
from image_packages import installed,sha
ROOT=Path(__file__).resolve().parents[1]

def profile():return json.loads((ROOT/'image/live-assembly.json').read_text())
def extent(iso,name):
 text=subprocess.check_output(['xorriso','-indev',str(iso),'-find',name,'-exec','report_lba','--'],text=True,stderr=subprocess.DEVNULL)
 pattern=r"^File data lba:\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'"+re.escape(name)+"'$"
 rows=[tuple(map(int,m.groups())) for line in text.splitlines() if (m:=re.fullmatch(pattern,line))]
 if not rows or [r[0] for r in rows]!=list(range(len(rows))) or any(r[3]!=rows[0][3] for r in rows):raise ValueError('Unsupported ISO extent layout: '+name)
 if any(b[1]!=a[1]+a[2] for a,b in zip(rows,rows[1:])):raise ValueError('Non-contiguous extents require explicit reconstruction')
 size=rows[0][3]
 if not size<=sum(r[2] for r in rows)*2048<size+2048:raise ValueError('Invalid ISO extent length')
 return rows[0][1]*2048,size

def digest_range(path,offset,size):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  f.seek(offset)
  while size:
   data=f.read(min(size,8*1024**2))
   if not data:raise ValueError('Truncated filesystem extent')
   h.update(data);size-=len(data)
 return h.hexdigest()

def verify_base(iso,development=False):
 p=profile();wanted=p['development_parent_sha256'] if development else p['official_iso_sha256']
 if Path(iso).is_symlink() or sha(iso)!=wanted:raise ValueError('Unrecognized parent ISO')
 offset,size=extent(iso,'/casper/filesystem.squashfs')
 if size!=p['base_filesystem_bytes'] or digest_range(iso,offset,size)!=p['base_filesystem_sha256']:raise ValueError('Application layer belongs to a different base filesystem')
 data=subprocess.check_output(['unsquashfs','-o',str(offset),'-cat',str(iso),'var/lib/dpkg/status'])
 if hashlib.sha256(data).hexdigest()!=p['base_status_sha256']:raise ValueError('Base package state mismatch')
 return offset,size

def squash_cat(image,name):return subprocess.check_output(['unsquashfs','-cat',str(image),name],stderr=subprocess.DEVNULL)

def blocks(text):
 result={}
 for block in text.strip().split('\n\n'):
  name=next((l[9:] for l in block.splitlines() if l.startswith('Package: ')),None)
  arch=next((l[14:] for l in block.splitlines() if l.startswith('Architecture: ')),None)
  if not name or not arch or name+':'+arch in result:raise ValueError('Malformed package database')
  result[name+':'+arch]=block
 return result

def verify_components(apps,components,report):
 p=profile();r=json.loads(Path(report).read_text())
 if sha(apps)!=p['app_layer_sha256']:raise ValueError('Unreviewed application artifact')
 app_status=squash_cat(apps,'var/lib/dpkg/status')
 if hashlib.sha256(app_status).hexdigest()!=p['app_status_sha256']:raise ValueError('Application status differs')
 if r.get('purpose')!='orez-dpkg-owned-components' or r.get('source_profile_sha256')!=sha(ROOT/'image/live-assembly.json') or r.get('application_status_sha256')!=p['app_status_sha256'] or sha(components)!=r.get('layer_sha256'):raise ValueError('Component provenance mismatch')
 status=squash_cat(components,'var/lib/dpkg/status');version=subprocess.check_output(['python3',str(ROOT/'build/package-info.py'),'version'],text=True).strip()
 if installed(status.decode())!={**installed(app_status.decode()),'orez-shell:all':version}:raise ValueError('Unexpected final package state')
 previous=blocks(app_status.decode());current=blocks(status.decode())
 if any(current.get(name)!=record for name,record in previous.items()):raise ValueError('Existing package records changed')
 payload={line for raw in (ROOT/'image/installer/installed-files.txt').read_text().splitlines() if (line:=raw.strip()) and not line.startswith('#')}
 metadata={'var/lib/dpkg/info/orez-shell.list','var/lib/dpkg/info/orez-shell.md5sums','var/lib/dpkg/status','var/lib/dpkg/status-old'}
 files=payload|metadata;directories={str(p) for name in files for p in PurePosixPath(name).parents if str(p)!='.'}
 listing=subprocess.check_output(['unsquashfs','-lln',str(components)],text=True)
 found=set()
 for line in listing.splitlines():
  fields=line.split(maxsplit=5)
  if len(fields)!=6 or not fields[5].startswith('squashfs-root'):continue
  mode,owner=fields[:2];name=fields[5].removeprefix('squashfs-root').lstrip('/')
  if owner!='0/0' or any(c in mode for c in 'sStT'):raise ValueError('Component ownership/privilege mismatch')
  if mode.startswith('d'):
   if name and name not in directories:raise ValueError('Unexpected component directory')
   if mode!='drwxr-xr-x':raise ValueError('Unsafe component directory mode')
  else:
   if name not in files or mode not in ['-rw-r--r--','-rwxr-xr-x']:raise ValueError('Unexpected component file/type/mode')
   found.add(name)
 if found!=files:raise ValueError('Missing component files')
 owned={line.lstrip('/') for line in squash_cat(components,'var/lib/dpkg/info/orez-shell.list').decode().splitlines()}
 if owned-directories-{'','.'}!=payload:raise ValueError('Unexpected dpkg-owned files')
 for name in payload:
  if squash_cat(components,name)!=(ROOT/'overlay'/name).read_bytes():raise ValueError('Stale component payload: '+name)
 if hashlib.sha256(status).hexdigest()!=r['installed_status_sha256']:raise ValueError('Status/report mismatch')
 return status,version

def brand_grub(text):
 if 'layerfs-path=' in text:raise ValueError('Explicit casper layer selection requires review')
 if text.count('Try or Install Kubuntu')!=1:raise ValueError('Unexpected upstream boot menu')
 text=text.replace('Try or Install Kubuntu','Try OREZ OS (installation unavailable)').replace('Kubuntu (safe graphics)','OREZ OS (safe graphics)')
 text,count=re.subn(r'menuentry "OEM install \(for manufacturers\)" \{[^{}]*\n\}', '',text)
 if count!=1:raise ValueError('Unrecognized upstream OEM entry')
 # The pinned upstream GRUB relies on initramfs defaults and omits this token.
 # OREZ's owner service/helper explicitly require it, so both UEFI menu paths
 # must supply it; otherwise the locked account can never be enrolled.
 text,count=re.subn(r'(^\s*linux\s+/casper/vmlinuz)(\s+)',r'\1 boot=casper\2',text,flags=re.MULTILINE)
 if count!=2:raise ValueError('Unexpected live kernel entries')
 return text
