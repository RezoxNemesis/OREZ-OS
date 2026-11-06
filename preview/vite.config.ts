import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  root: fileURLToPath(new URL('.', import.meta.url)),
  base: './',
  build: { outDir: '../dist/preview', emptyOutDir: true },
  plugins: [{
    name: 'orez-offline-preview',
    generateBundle(_options, bundle) {
      // Include hashed assets and public assets. No remote fonts, telemetry or APIs.
      const files = ['index.html', 'manifest.webmanifest', 'icon.svg', 'orez-ink.svg', 'orez-rest.jpg', ...Object.keys(bundle).filter(k => k !== 'index.html')];
      this.emitFile({ type: 'asset', fileName: 'sw.js', source: `
const NAMESPACE = 'orez-preview:' + self.registration.scope + ':';
const CACHE = NAMESPACE + 'v2-' + ${JSON.stringify(Object.keys(bundle).join('-'))};
const PREFIX = new URL('.', self.location.href).pathname;
const FILES = ${JSON.stringify(files)}.map(p => new URL(p, self.registration.scope).href);
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES))));
self.addEventListener('activate', e => e.waitUntil(Promise.all([
  caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith(NAMESPACE) && k !== CACHE).map(k => caches.delete(k)))),
  self.clients.claim()
])));
self.addEventListener('message', e => { if (e.data === 'ACTIVATE_UPDATE') self.skipWaiting(); });
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== self.location.origin || !url.pathname.startsWith(PREFIX)) return;
  e.respondWith(caches.open(CACHE).then(async cache => {
    // Only our public build assets are cached. Ignore Vary: Origin emitted by
    // preview servers: module requests and precache requests differ in Origin.
    const found = FILES.includes(url.href) ? await cache.match(url.href, {ignoreVary:true}) : undefined;
    if (found) return found;
    try { return await fetch(e.request); }
    catch (err) {
      if (e.request.mode === 'navigate') return cache.match(new URL('index.html', self.registration.scope).href);
      throw err;
    }
  }));
});
` });
    }
  }]
});
