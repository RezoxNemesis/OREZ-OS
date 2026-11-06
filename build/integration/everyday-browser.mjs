// Actual Brave, with its sandbox required. Never disable it to force a pass.
import {chromium} from '/opt/orez-qa/node_modules/playwright-core/index.mjs';
import {writeFile, readFile} from 'node:fs/promises';
import http from 'node:http';
const results=[];
let browser;
try {
  browser=await chromium.launch({executablePath:'/usr/bin/brave-browser',headless:false,chromiumSandbox:true,
    args:['--ozone-platform=wayland','--no-first-run','--no-default-browser-check'],timeout:25000});
  const context=await browser.newContext({viewport:{width:1280,height:720},acceptDownloads:true});
  const page=await context.newPage();
  async function scenario(name,action){
    try {results.push({name,status:'passed',detail:await action()});}
    catch(error){results.push({name,status:'blocked',error:String(error)});}
    try {await page.screenshot({path:`/evidence/${name}.png`,fullPage:true});}catch{}
  }
  await scenario('brave-sandbox-status',async()=>{await page.goto('chrome://sandbox');const text=await page.locator('body').innerText();await writeFile('/evidence/brave-sandbox.txt',text);return text;});
  await scenario('brave-public-browsing',async()=>{const response=await page.goto('https://www.wikipedia.org',{waitUntil:'domcontentloaded',timeout:25000});if(!response?.ok())throw Error('HTTP '+response?.status());return {title:await page.title(),url:page.url()};});
  await scenario('brave-youtube',async()=>{
    await page.goto('https://www.youtube.com/watch?v=aqz-KE-bpKQ',{waitUntil:'domcontentloaded',timeout:25000});
    const video=page.locator('video');await video.waitFor({timeout:15000});
    const before=await video.evaluate(v=>{v.muted=true;return v.currentTime;});
    await video.evaluate(v=>v.play());await page.waitForTimeout(4000);
    const after=await video.evaluate(v=>({time:v.currentTime,width:v.videoWidth,ready:v.readyState}));
    if(after.time<=before+1||after.width===0)throw Error('No advancing decoded YouTube video');return after;
  });
  const bytes=Buffer.from('OREZ browser download integrity fixture\n');
  const server=http.createServer((req,res)=>{if(req.url==='/download'){res.writeHead(200,{'Content-Type':'application/octet-stream','Content-Disposition':'attachment; filename="orez-download.txt"'});res.end(bytes);}else{res.writeHead(200,{'Content-Type':'text/html'});res.end('<!doctype html><title>OREZ download check</title><h1>Local browser download integrity test</h1><a href="/download">Download test file</a>');}});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  await scenario('brave-file-download',async()=>{await page.goto(`http://127.0.0.1:${server.address().port}`);const pending=page.waitForEvent('download');await page.getByRole('link').click();const d=await pending;await d.saveAs('/evidence/browser-download.txt');if(!bytes.equals(await readFile('/evidence/browser-download.txt')))throw Error('Downloaded bytes differ');return {name:d.suggestedFilename(),bytes:bytes.length,source:'local HTTP fixture; not a Play Store app download'};});
  await new Promise(resolve=>server.close(resolve));
} catch(error) {
  results.push({name:'brave-sandbox-startup',status:'blocked',error:String(error),policy:'No --no-sandbox, privileged container or host security-policy changes permitted.'});
} finally {
  if(browser)await browser.close();
  await writeFile('/evidence/browser-results.json',JSON.stringify(results,null,2));
  console.log(JSON.stringify(results,null,2));
}
