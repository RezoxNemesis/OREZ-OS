import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
const server=spawn('node',['node_modules/vite/bin/vite.js','preview','--config','preview/vite.config.ts','--port','4180','--host','127.0.0.1','--strictPort'],{stdio:'ignore'});
let browser;
try {
  for(let i=0;i<30;i++){try{if((await fetch('http://127.0.0.1:4180/')).ok)break;}catch{} await new Promise(r=>setTimeout(r,200));}
  browser=await chromium.launch({executablePath:'/usr/bin/chromium'});
  const context=await browser.newContext();
  context.on('serviceworker', worker=>{console.log('WORKER',worker.url()); worker.on('console', msg=>console.log('WORKER CONSOLE',msg.type(),msg.text()));});
  const page=await context.newPage();
  page.on('console',msg=>console.log('PAGE CONSOLE',msg.type(),msg.text()));
  page.on('pageerror',error=>console.log('ERROR',error.message));
  page.on('requestfailed',req=>console.log('REQUEST FAILED',req.url(),req.failure()));
  await page.goto('http://127.0.0.1:4180/');
  console.log('REGISTRATION', await page.evaluate(async () => {
    try { const r=await navigator.serviceWorker.register('./sw.js'); return {scope:r.scope}; }
    catch(e) { return {name:e.name,message:e.message}; }
  }));
  for(let i=0;i<4;i++){
    await new Promise(r=>setTimeout(r,1000));
    console.log(await page.evaluate(async()=>({
      registrations: (await navigator.serviceWorker.getRegistrations()).map(r=>({scope:r.scope,active:r.active?.state,installing:r.installing?.state,waiting:r.waiting?.state})),
      caches: await caches.keys(), controller: navigator.serviceWorker.controller?.state,
      status: document.querySelector('[role=status]')?.textContent
    })));
  }
  console.log(await page.evaluate(async()=>{
    const files=['index.html','manifest.webmanifest','icon.svg','orez-ink.svg',...Array.from(document.querySelectorAll('script[src],link[rel=stylesheet]')).map(n=>n.getAttribute('src')||n.getAttribute('href'))];
    return await Promise.all(files.map(async f=>{ const r=await fetch(f); return [f,r.status,r.headers.get('content-type')]; }));
  }));
  await page.screenshot({path:'dist/diagnostics/offline-debug.png',fullPage:true});
  if(!await page.evaluate(()=>!!navigator.serviceWorker.controller)) process.exitCode=1;
}finally{await browser?.close();server.kill();}
