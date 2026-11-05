/* Project-local PWA cache. Offline launches display a connection notice. */
'use strict';
const VERSION = "bc41d8a03b1f62a9";
const APP = "Velvitty";
const CORE = ["./manifest.webmanifest", "./pwa.js", "./offline.html", "./pwa-icon-192.png", "./pwa-icon-512.png", "./pwa-icon-maskable.png", "./apple-touch-icon.png"];
const OPTIONAL = [];
const SCOPE = self.registration.scope;
const UI_SOURCE = "./index.html";
const PREFIX = 'velvitty-pwa:' + APP + ':' + encodeURIComponent(SCOPE) + ':';
const SHELL = PREFIX + VERSION + ':shell';
const RUNTIME = PREFIX + VERSION + ':runtime';
const absolute = path => new URL(path, SCOPE).href;
const FRAME_ENTRY = null;
const isCore = new Set(CORE.map(absolute));
const MAX_ENTRIES = 64;
const MAX_BYTES = 4 * 1024 * 1024;

const UI_URL = new URL('./pwa-ui.html', SCOPE).href;
function uiOnly(source) {
  source = source.replace(/<script\b[^>]*>[\s\S]*?<\/script\s*>/gi, '');
  source = source.replace(/<(?:iframe|object)\b[^>]*>[\s\S]*?<\/(?:iframe|object)\s*>/gi, '');
  source = source.replace(/<(?:base|embed)\b[^>]*>/gi, '');
  source = source.replace(/<meta\b(?=[^>]*http-equiv\s*=\s*["']?refresh)[^>]*>/gi, '');
  source = source.replace(/\s+on[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '');
  const policy = `<base href="${new URL(UI_SOURCE, SCOPE).href}"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; connect-src 'none'; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' data: https:; frame-src 'none'; object-src 'none'; form-action 'none'; base-uri 'self'"><style>html{pointer-events:none!important}*{animation-play-state:paused!important;caret-color:transparent!important}</style>`;
  source = source.replace(/<head\b[^>]*>/i, tag => tag + policy);
  return source.replace(/<body\b/i, '<body inert');
}
async function saveStaticUI(response) {
  if (!response.ok || response.redirected || !response.headers.get('content-type')?.includes('text/html')) return;
  if (Number(response.headers.get('content-length') || 0) > MAX_BYTES) return;
  const html = await response.text();
  if (html.length > MAX_BYTES) return;
  const cache = await caches.open(SHELL);
  await cache.put(UI_URL, new Response(uiOnly(html), {headers: {'Content-Type': 'text/html; charset=utf-8'}}));
}
async function refreshUI() {
  try {
    await saveStaticUI(await fetch(new URL(UI_SOURCE, SCOPE), {cache: 'no-store'}));
  } catch (_) { /* Preserve the last static UI background when the network is down. */ }
}

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(SHELL);
    await cache.addAll(CORE.map(path => new Request(absolute(path), {cache: 'reload'})));
    if (FRAME_ENTRY) await cache.add(new Request(FRAME_ENTRY, {cache: 'reload'}));
    await refreshUI();
    // Optional documentation can fail independently without disabling the app shell.
    await Promise.allSettled(OPTIONAL.map(async path => {
      const response = await fetch(new Request(absolute(path), {cache: 'reload'}));
      if (response.ok && !response.redirected && Number(response.headers.get('content-length') || 0) <= MAX_BYTES) await cache.put(absolute(path), response);
    }));
  })());
  // An update waits until open work is closed, or the user presses Update.
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(name => name.startsWith(PREFIX) && name !== SHELL && name !== RUNTIME).map(name => caches.delete(name)));
    
    await self.clients.claim();
  })());
});
self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data?.type === 'REFRESH_UI') event.waitUntil(refreshUI());
});
async function cached(key) {
  return (await caches.open(RUNTIME)).match(key).then(value => value || caches.open(SHELL).then(cache => cache.match(key)));
}
async function remember(key, response) {
  if (!response.ok || response.redirected || response.status === 206 || !['basic', 'default'].includes(response.type)) return;
  if (Number(response.headers.get('content-length') || 0) > MAX_BYTES) return;
  if ((await response.clone().arrayBuffer()).byteLength > MAX_BYTES) return;
  if (/no-store|private/i.test(response.headers.get('cache-control') || '')) return;
  const cache = await caches.open(RUNTIME);
  await cache.put(key, response);
  const keys = await cache.keys();
  await Promise.all(keys.slice(0, Math.max(0, keys.length - MAX_ENTRIES)).map(old => cache.delete(old)));
}
async function connectionNotice() {
  const notice = await caches.match(absolute('./offline.html'), {cacheName: SHELL});
  return notice || new Response(
    '인터넷 연결 상태가 불안정하여 어플리케이션을 실행할 수 없습니다. 네트워크 환경을 확인해 주세요.',
    {status: 503, headers: {'Content-Type': 'text/plain; charset=utf-8'}}
  );
}

async function navigation(request, key, event) {
  if (self.navigator?.onLine === false) return connectionNotice();

  // Only cache the small entry shell for apps that have a separate main document.
  if (key === FRAME_ENTRY) {
    const entry = await caches.match(FRAME_ENTRY, {cacheName: SHELL});
    if (entry) return entry;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 2500);
  const network = fetch(request, {cache: 'no-store', signal: controller.signal});
  if (key === absolute(UI_SOURCE) && !new URL(request.url).search) {
    event.waitUntil(network.then(response => saveStaticUI(response.clone())).catch(() => {}));
  }
  try {
    return await network;
  } catch (_) {
    return connectionNotice();
  } finally {
    clearTimeout(timer);
  }
}
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== new URL(SCOPE).origin || request.headers.has('range')) return;
  if (url.href === UI_URL) {
    event.respondWith(caches.open(SHELL).then(async cache => await cache.match(UI_URL) || new Response('<!doctype html><body style=\"margin:0;background:#15151f\"></body>', {headers: {'Content-Type': 'text/html; charset=utf-8'}})));
    return;
  }
  if (!url.href.startsWith(SCOPE)) return;
  if (/\/(?:api|graphql|auth|login|logout)(?:\/|$)/i.test(url.pathname)) return;
  const keyURL = new URL(url);
  keyURL.hash = '';
  if (request.mode === 'navigate') {
    // Query strings can contain private image codes. Cache static HTML by path only.
    keyURL.search = '';
    if (keyURL.href === SCOPE) keyURL.pathname += 'index.html';
    event.respondWith(navigation(request, keyURL.href, event));
    return;
  }
  if (!isCore.has(url.href) && (url.search || !/\.(?:html|js|mjs|css|png|jpe?g|webp|svg|ico|woff2?|webmanifest)$/i.test(url.pathname))) return;
  const refresh = fetch(request).then(async response => { await remember(url.href, response.clone()); return response; });
  event.waitUntil(refresh.then(() => {}).catch(() => {}));
  event.respondWith((async () => await cached(url.href) || await refresh)());
});
