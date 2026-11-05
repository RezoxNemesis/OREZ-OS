// Portable design preview for phone download; not an OS image or Android APK.
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
const root='dist/preview';
const noticeParts = ['OREZ preview: original OREZ source and artwork remain owner-reserved.\nThird-party software keeps its own licences.\n'];
for (const [name, licence] of [['react','LICENSE'], ['react-dom','LICENSE'], ['scheduler','LICENSE'], ['vite','LICENSE.md']]) {
  const metadata = JSON.parse(await readFile(`node_modules/${name}/package.json`, 'utf8'));
  noticeParts.push(`\n${name} ${metadata.version}\n${await readFile(`node_modules/${name}/${licence}`, 'utf8')}`);
}
const notices = noticeParts.join('\n');
await writeFile(path.join(root, 'THIRD_PARTY_NOTICES.txt'), notices);
let html=(await readFile(path.join(root,'index.html'),'utf8')).replace('<html lang="en">','<html lang="en" data-portable="true">');
const script=html.match(/<script[^>]*src="([^"]+)"[^>]*><\/script>/);
const stylesheet=html.match(/<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/);
if(!script || !stylesheet) throw new Error('Built JS and CSS entrypoints were not found');
let css=await readFile(path.join(root,stylesheet[1]),'utf8');
const matches=[...css.matchAll(/url\(([^)]+\.(?:svg|jpg))\)/g)];
for(const match of matches){
  const file=match[1].replace(/^['"]|['"]$/g,'');
  const resolved=path.resolve(root,path.dirname(stylesheet[1]),file);
  const data=(await readFile(resolved)).toString('base64');
  css=css.replace(match[0],`url(data:${file.endsWith('.jpg') ? 'image/jpeg' : 'image/svg+xml'};base64,${data})`);
}
const js=await readFile(path.join(root,script[1]),'utf8');
html=html.replace(script[0],()=>`<script type="module">${js.replace(/<\/script/gi,'<\\/script')}</script>`)
  .replace(stylesheet[0],()=>`<style>${css}</style>`)
  .replace(/<link[^>]+rel="(?:icon|manifest)"[^>]*>/g,'');
// Preserve dependency notices in the portable file as well as the hosted bundle.
html = html.replace('</html>', `<!-- THIRD-PARTY NOTICES\n${notices.replace(/--/g, '—')}\n--></html>`);
await writeFile('dist/OREZ-Preview.html',html);
await writeFile(path.join(root,'portable.html'),html);
console.log('Exported dist/OREZ-Preview.html — standalone browser design preview, not an OS.');
