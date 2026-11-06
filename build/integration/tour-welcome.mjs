// Render the actual shipped local help document, not a native Brave/boot claim.
import { chromium } from '@playwright/test';
import {existsSync} from 'node:fs';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
const out=process.env.OREZ_EVIDENCE_DIR;
if(!out)throw Error('Use the evidence runner');
const executablePath=process.env.OREZ_CHROMIUM||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined);
const browser=await chromium.launch({executablePath,headless:true});
try {
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 await page.route('http**://**/*',r=>r.abort());
 // Render only this known project document in memory, as the report renderer
 // does. This does not test file:// navigation or change browser policy.
 await page.setContent(await readFile('overlay/usr/share/doc/orez/welcome.html','utf8'));
 if(!await page.getByText('Live-test candidate only.',{exact:true}).isVisible())throw Error('Missing qualification warning');
 await page.screenshot({path:path.join(out,'welcome-document-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile horizontal overflow');
 await page.screenshot({path:path.join(out,'welcome-document-phone.png'),fullPage:true});
 console.log('PASS: actual local welcome document rendered at desktop and phone widths, warning visible, no horizontal overflow. Host Playwright capture, not native Brave or booted OS.');
}finally{await browser.close();}
