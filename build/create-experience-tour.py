#!/usr/bin/env python3
"""Package original screenshots and a labeled, offline, phone-readable OS tour."""
import argparse,hashlib,html,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False);(a.output/'images').mkdir();(a.output/'records').mkdir()
root=Path('dist/evidence');spec=json.loads(Path('docs/experience/tour.json').read_text());ideas=json.loads(Path('docs/experience/ideas.json').read_text())
assert len(ideas['categories'])==9 and all(len(c['ideas'])==5 for c in ideas['categories'])
paths=sorted(root.glob('qa10-*'));references=[];images={};runs=[]
for folder in paths:
    result=folder/'result.json'
    if not result.exists():raise SystemExit('Incomplete test run: '+str(folder))
    record=json.loads(result.read_text());record['directory']=folder.name;runs.append(record)
    for item in [result,folder/'output.log',folder/'screenshots.json']:
        if item.is_file():shutil.copyfile(item,a.output/'records'/(folder.name+'-'+item.name))
    for image in sorted(folder.rglob('*.png')):
        digest=hashlib.sha256(image.read_bytes()).hexdigest();images.setdefault(digest,image)
        references.append({'source':str(image.relative_to(root)),'sha256':digest,'bytes':image.stat().st_size})
for stop in spec['stops']:
    image=root/stop['source'];digest=hashlib.sha256(image.read_bytes()).hexdigest();images.setdefault(digest,image)
    stop['sha256']=digest;stop['image']='images/'+digest+'.png'
    if not any(r['source']==stop['source'] for r in references):references.append({'source':stop['source'],'sha256':digest,'bytes':image.stat().st_size,'historical':True})
for digest,image in images.items():shutil.copyfile(image,a.output/'images'/(digest+'.png'))
manifest={'scope':spec['scope'],'unique_images':len(images),'capture_references':len(references),'references':references,'runs':runs,'tour':spec['stops']}
(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
esc=html.escape
style='''body{font:17px/1.65 system-ui,sans-serif;background:#f7f5f0;color:#202020;margin:0}main{max-width:1050px;margin:auto;padding:24px}h1{font-size:clamp(2rem,5vw,3.2rem);font-weight:500}h2{margin-top:2rem}a{color:#254963}img{display:block;max-width:100%;height:auto;background:#ddd;border-radius:8px}figure{margin:20px 0}figcaption{font-size:.9rem;overflow-wrap:anywhere;margin:12px 0}.card,details{background:white;border:1px solid #c9c5bd;border-radius:16px;padding:22px;margin:22px 0}.tag{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}.note{border-left:4px solid #78634a;padding-left:16px}summary{cursor:pointer;font-weight:650}nav{display:flex;flex-wrap:wrap;gap:12px}li{margin:10px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.65 system-ui}button,a,summary{touch-action:manipulation}:focus-visible{outline:3px solid #335a77;outline-offset:4px}@media(max-width:550px){main{padding:14px}.card,details{padding:16px}}'''
head=lambda title:'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>'+style+'</style><main>'
body=[head('OREZ OS — actual experience tour'),'<div class="tag">Engineering tour · 6 November 2026</div><h1>Welcome to OREZ.</h1><p>A practical look at the desktop components we can run today, and a clear account of what remains.</p><p class="note"><strong>Not an install-ready OS.</strong> Native container screens, SDDM test mode, a local document render and historical VM evidence are labeled individually. No screenshot certifies this PC, a completed installation, real Wi-Fi or phone mirroring.</p><nav><a href="#journey">First boot &amp; answers</a><a href="#tour">Screen tour</a><a href="#ideas">45 future ideas</a><a href="all-captures.html">Every capture, including failures</a><a href="manifest.json">Evidence manifest</a></nav>']
body+=['<details id="journey"><summary>Boot, passwords, internet, storage and Linux explained</summary><pre>'+esc(Path('docs/FIRST_BOOT_AND_TOUR.md').read_text())+'</pre></details>','<h2 id="tour">The practical tour</h2>']
for i,s in enumerate(spec['stops'],1):
    body.append('<section class="card" id="screen-'+str(i)+'"><div class="tag">'+esc(s['kind'])+'</div><h2>'+str(i)+'. '+esc(s['title'])+'</h2><p>'+esc(s['caption'])+'</p><figure><a href="'+s['image']+'"><img loading="lazy" src="'+s['image']+'" alt="'+esc(s['title'])+'"></a><figcaption>'+esc(s['source'])+'</figcaption></figure></section>')
body.append('<section class="card"><h2>Not yet available to show working</h2><p>Completed installation/reboot, disk-encryption unlock, recovery/rollback, NVIDIA acceleration, real Wi-Fi/Bluetooth/USB transfers, scrcpy phone mirroring and OREZ AI. Their implementation or hardware qualification remains open. The native Brave sandbox is blocked by the test environment. YouTube is optional under the latest owner direction.</p></section><h2 id="ideas">45 future ideas</h2><p>Proposals, not implemented or tested features; related concepts may exist elsewhere. Boot, installation, updates and recovery take priority.</p>')
for c in ideas['categories']:
    body.append('<details><summary>'+esc(c['title'])+' — five ideas</summary>')
    for idea in c['ideas']:body.append('<h3>'+esc(idea['title'])+'</h3><p>'+esc(idea['description'])+'</p><p><strong>Engineering:</strong> '+esc(idea['engineering'])+'</p><p><strong>Future acceptance:</strong> '+esc(idea['acceptance'])+'</p>')
    body.append('</details>')
body.append('<p><a href="all-captures.html">Open all '+str(len(images))+' original PNGs and test results.</a></p></main></html>')
(a.output/'index.html').write_text(''.join(body))
markdown=['# OREZ OS — actual screen tour\n\n29 labeled stops. Native component captures are not an installed OS. Download/extract the ZIP and open index.html for the phone-friendly version. The 45 future ideas are in [EXPERIENCE_IDEAS.md](EXPERIENCE_IDEAS.md); boot/password/storage answers are in [FIRST_BOOT_AND_TOUR.md](FIRST_BOOT_AND_TOUR.md).\n']
for i,s in enumerate(spec['stops'],1):
    markdown.append('\n## '+str(i)+'. '+s['title']+'\n\n**'+s['kind']+'**\n\n'+s['caption']+'\n\n!['+s['title']+']('+s['image']+')\n')
(a.output/'TOUR.md').write_text(''.join(markdown))
allbody=[head('OREZ — every retained capture'),'<h1>Every retained capture</h1><p><a href="index.html">Return to the guided tour</a></p><p>Includes failures and intermediate states. Report images are not OS screens. Consult manifest.json for source identity, status and exact image hashes.</p>']
for r in runs:allbody.append('<p>'+esc(r['directory']+': '+r['status']+' — '+r['name'])+'</p>')
for digest,image in images.items():
    source=str(image.relative_to(root));kind='Test report' if image.name.startswith('report-') else 'Historical VM capture' if not source.startswith('qa10-') else 'Local HTML document render' if 'welcome-document' in source else 'Tour-gallery render' if 'gallery' in source else 'Native container screenshot'
    allbody.append('<figure><figcaption>'+esc(kind+' — '+source)+'</figcaption><a href="images/'+digest+'.png"><img loading="lazy" src="images/'+digest+'.png" alt="'+esc(kind)+'"></a></figure>')
allbody.append('</main></html>');(a.output/'all-captures.html').write_text(''.join(allbody))
for name in ['FIRST_BOOT_AND_TOUR.md','EXPERIENCE_IDEAS.md']:shutil.copyfile(Path('docs')/name,a.output/name)
(a.output/'README.md').write_text('# OREZ OS experience tour\n\nDownload the ZIP, extract it, and open index.html. All captures are original .png images under images/. all-captures.html includes failed attempts; manifest.json records hashes and scope. This is not an OS download or installation approval.\n')
print(json.dumps({'directory':str(a.output),'unique_images':len(images),'capture_references':len(references),'runs':len(runs),'tour_stops':len(spec['stops']),'ideas':45},indent=2))
