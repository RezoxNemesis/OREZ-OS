// Gallery acceptance only; never label these web captures as a running OREZ OS.
import {chromium} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {existsSync} from 'node:fs';
import path from 'node:path';
const out=process.env.OREZ_EVIDENCE_DIR;if(!out)throw Error('Evidence runner required');
const root='dist/tour-preview';const manifest=JSON.parse(await readFile(path.join(root,'manifest.json'),'utf8'));
for(const ref of manifest.references){
 const data=await readFile(path.join(root,'images',ref.sha256+'.png'));
 if(createHash('sha256').update(data).digest('hex')!==ref.sha256||data.readUInt32BE(0)!==0x89504e47)throw Error('Image integrity failure');
}
const browser=await chromium.launch({executablePath:process.env.OREZ_CHROMIUM||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),headless:true});
try{
 const page=await browser.newPage();
 await page.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:4183/')?r.continue():r.abort());
 for(const [name,width,height] of [['desktop',1440,1000],['phone',390,844]]){
  await page.setViewportSize({width,height});await page.goto('http://127.0.0.1:4183/',{waitUntil:'networkidle'});
  if(await page.locator('section[id^="screen-"]').count()!==29)throw Error('Missing tour stops');
  if(await page.locator('h3').count()!==45)throw Error('Missing ideas');
  await page.locator('#journey summary').click();
  if(!await page.getByText('What the finished installation should ask',{exact:false}).isVisible())throw Error('First boot details missing');
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow');
  await page.locator('#journey summary').click();
  await page.screenshot({path:path.join(out,'gallery-'+name+'.png')});
 }
 for(const image of manifest.tour){const r=await page.request.get('http://127.0.0.1:4183/'+image.image);if(r.status()!==200)throw Error('Missing tour image');}
 console.log(JSON.stringify({scope:'Gallery web UI, not OS functionality',viewports:2,tour_stops:29,ideas:45,verified_image_references:manifest.references.length,all_tour_images_http:200,no_horizontal_overflow:true}));
}finally{await browser.close();}
