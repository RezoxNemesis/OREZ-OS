import { chromium } from '@playwright/test';
import { readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';

const dir = path.resolve(process.argv[2] || 'dist/evidence');
const result = JSON.parse(await readFile(path.join(dir, 'result.json'), 'utf8'));
const raw = await readFile(path.join(dir, 'output.log'), 'utf8');
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cleaned = raw.replace(/\x1b\[[0-9;]*[A-Za-z]/g, '').replace(/\r/g, '\n');
const lines = cleaned.split('\n');
// Wrap long lines before pagination so screenshots never hide horizontal text.
const wrapped = lines.flatMap(line => line.length ? Array.from({length: Math.ceil(line.length / 118)}, (_, i) => line.slice(i * 118, (i + 1) * 118)) : ['']);
const pages = Array.from({length: Math.max(1, Math.ceil(wrapped.length / 42))}, (_, i) => wrapped.slice(i * 42, (i + 1) * 42));
const style = `body{margin:0;background:#f6f4ef;color:#161616;font:16px/1.5 system-ui,sans-serif}main{max-width:1240px;margin:auto;padding:44px}header{border-bottom:1px solid #aaa;padding-bottom:20px}h1{font-size:29px;margin:10px 0}.eyebrow{font-size:12px;letter-spacing:2px}small{color:#555}pre{font:14px/1.48 monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#fff;padding:24px;border:1px solid #ddd;border-radius:12px}.meta{font:12px/1.7 monospace;overflow-wrap:anywhere}.status{font-weight:700}a{color:inherit}img{max-width:100%;border:1px solid #ccc}figure{margin:26px 0}`;
const header = `<header><div class="eyebrow">OREZ OS / ENGINEERING EVIDENCE</div><h1>${escape(result.name)}</h1><p class="status">${escape(result.status.toUpperCase())} · ${escape(result.kind)} · ${result.duration_seconds}s · exit ${result.exit_code}</p><p>This is a captured test report. It is not a running desktop or hardware certification.</p><div class="meta">Commit: ${escape(result.commit)}<br>Source SHA-256: ${escape(result.source_digest)}<br>Started (UTC): ${escape(result.started_at)}<br>Command: ${escape(result.command.join(' '))}</div></header>`;
const executablePath = process.env.OREZ_CHROMIUM || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
const browser = await chromium.launch({executablePath, headless:true, args:['--disable-dev-shm-usage']});
const screenshots = [];
try {
  const page = await browser.newPage({viewport:{width:1440,height:1200}, deviceScaleFactor:1});
  for (let i=0;i<pages.length;i++) {
    const name = `report-${String(i+1).padStart(3,'0')}`;
    const html = `<!doctype html><html lang="en"><meta charset="utf-8"><title>${escape(result.name)}</title><style>${style}</style><main>${header}<p>Output page ${i+1} of ${pages.length}</p><pre>${escape(pages[i].join('\n'))}</pre></main></html>`;
    await writeFile(path.join(dir, `${name}.html`), html);
    // Render our escaped, self-contained report without file:// navigation.
    await page.setContent(html, {waitUntil:'load'});
    await page.screenshot({path:path.join(dir,`${name}.png`),fullPage:true});
    screenshots.push(`${name}.png`);
  }
} finally { await browser.close(); }
await writeFile(path.join(dir,'screenshots.json'), JSON.stringify({kind:'test-report',screenshots},null,2)+'\n');
await writeFile(path.join(dir,'index.html'),`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${escape(result.name)}</title><style>${style}</style><main>${header}<p><a href="result.json">Machine-readable result</a> · <a href="output.log">Complete log</a></p>${screenshots.map((s,i)=>`<figure><figcaption>Report page ${i+1}</figcaption><a href="${s}"><img src="${s}" alt="Test report page ${i+1}" loading="lazy"></a></figure>`).join('')}</main></html>`);
console.log(`Captured ${screenshots.length} report screenshots in ${dir}`);
