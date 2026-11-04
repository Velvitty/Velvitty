/* Velvitty PWA controls. No analytics; application files remain in the browser. */
(() => {
  'use strict';
  if (!/^https?:$/.test(location.protocol) || !('serviceWorker' in navigator)) return;
  const ownScript = document.currentScript;
  const base = new URL('./', ownScript.src);
  const english = () => document.documentElement.lang.startsWith('en');
  const words = (ko, en) => english() ? en : ko;
  let installEvent = null;
  let registration = null;
  let reloading = false;
  let ready = false;
  const CONNECTION_MESSAGE = "인터넷 연결 상태가 불안정하여 어플리케이션을 실행할 수 없습니다. 네트워크 환경을 확인해 주세요.";
  function installGlassLens(root) {
    const doc = root.ownerDocument || root;
    const glass = root.querySelector('.glass');
    const backdrop = root.querySelector('.app-backdrop');
    if (!glass || !backdrop || glass.querySelector('.lens-optics')) return;
    // Sandboxed background frames cannot rely on service-worker navigation.
    // Read only this application's saved UI and embed it without a network request.
    backdrop.removeAttribute('src');
    const uiScope = new URL('./', location.href).href;
    readStaticUIFromCache(uiScope).then(html => { if (html) backdrop.srcdoc = html; }).catch(() => {});
    const optics = doc.createElement('div');
    optics.className = 'lens-optics';
    optics.setAttribute('aria-hidden', 'true');
    const replica = doc.createElement('div');
    replica.className = 'lens-copy';
    replica.inert = true;
    const uiRoot = replica.attachShadow({mode: 'open'});
    optics.append(replica);
    const clip = doc.createElement('div');
    clip.className = 'lens-clip';
    clip.append(optics);
    glass.prepend(clip);
    const ns = 'http://www.w3.org/2000/svg';
    const id = 'pwa-glass-lens-' + Math.random().toString(36).slice(2);
    const svg = doc.createElementNS(ns, 'svg');
    svg.setAttribute('width', '0');
    svg.setAttribute('height', '0');
    svg.setAttribute('aria-hidden', 'true');
    svg.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden;pointer-events:none';
    const defs = doc.createElementNS(ns, 'defs');
    const filter = doc.createElementNS(ns, 'filter');
    filter.id = id;
    filter.setAttribute('filterUnits', 'userSpaceOnUse');
    filter.setAttribute('x', '0');
    filter.setAttribute('y', '0');
    filter.setAttribute('color-interpolation-filters', 'sRGB');
    const map = doc.createElementNS(ns, 'feImage');
    map.setAttribute('result', 'normal');
    map.setAttribute('preserveAspectRatio', 'none');
    filter.append(map);
    const frost = doc.createElementNS(ns, 'feGaussianBlur');
    frost.setAttribute('in', 'SourceGraphic');
    frost.setAttribute('stdDeviation', '8.5');
    frost.setAttribute('result', 'frosted-ui');
    filter.append(frost);
    const channels = [
      ['r', 72, '1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0'],
      ['g', 64, '0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0'],
      ['b', 56, '0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0']
    ];
    for (const [channel, scale, values] of channels) {
      const displace = doc.createElementNS(ns, 'feDisplacementMap');
      displace.setAttribute('in', 'frosted-ui');
      displace.setAttribute('in2', 'normal');
      displace.setAttribute('scale', scale);
      displace.setAttribute('xChannelSelector', 'R');
      displace.setAttribute('yChannelSelector', 'G');
      displace.setAttribute('result', channel + '-displaced');
      const color = doc.createElementNS(ns, 'feColorMatrix');
      color.setAttribute('in', channel + '-displaced');
      color.setAttribute('values', values);
      color.setAttribute('result', channel);
      filter.append(displace, color);
    }
    const blendRG = doc.createElementNS(ns, 'feBlend');
    blendRG.setAttribute('in', 'r');
    blendRG.setAttribute('in2', 'g');
    blendRG.setAttribute('mode', 'screen');
    blendRG.setAttribute('result', 'rg');
    const blendRGB = doc.createElementNS(ns, 'feBlend');
    blendRGB.setAttribute('in', 'rg');
    blendRGB.setAttribute('in2', 'b');
    blendRGB.setAttribute('mode', 'screen');
    filter.append(blendRG, blendRGB);
    defs.append(filter);
    svg.append(defs);
    doc.body.append(svg);
    const canvas = doc.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let previous = '';
    let scheduled = false;
    function update() {
      scheduled = false;
      const box = optics.getBoundingClientRect();
      const w = Math.max(1, Math.ceil(box.width));
      const h = Math.max(1, Math.ceil(box.height));
      replica.style.filter = 'blur(' + Math.min(10, Math.max(7, w * .014)) + 'px)';
      replica.style.width = (innerWidth + 10) + 'px';
      replica.style.height = (innerHeight + 10) + 'px';
      replica.style.left = (-box.left - 5) + 'px';
      replica.style.top = (-box.top - 5) + 'px';
      const size = w + ':' + h;
      if (size === previous) return;
      previous = size;
      canvas.width = w;
      canvas.height = h;
      const image = ctx.createImageData(w, h);
      const radius = Math.min(32, w / 2, h / 2);
      const bevel = Math.min(28, w * .08, h * .08);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const dx = x + .5 - w / 2;
        const dy = y + .5 - h / 2;
        const qx = Math.abs(dx) - (w / 2 - radius);
        const qy = Math.abs(dy) - (h / 2 - radius);
        const ox = Math.max(qx, 0);
        const oy = Math.max(qy, 0);
        const length = Math.hypot(ox, oy);
        const distance = Math.min(Math.max(qx, qy), 0) + length - radius;
        let nx = 0, ny = 0;
        if (length > 0) { nx = Math.sign(dx) * ox / length; ny = Math.sign(dy) * oy / length; }
        else if (qx > qy) nx = Math.sign(dx); else ny = Math.sign(dy);
        const edge = Math.max(0, Math.min(1, 1 + distance / bevel));
        const bend = 18 * edge * edge * (2 - edge);
        const shiftX = -nx * bend - dx * .012;
        const shiftY = -ny * bend - dy * .012;
        const p = (y * w + x) * 4;
        image.data[p] = Math.max(0, Math.min(255, 128 + shiftX * 127 / 32));
        image.data[p + 1] = Math.max(0, Math.min(255, 128 + shiftY * 127 / 32));
        image.data[p + 2] = 128;
        image.data[p + 3] = 255;
      }
      ctx.putImageData(image, 0, 0);
      map.setAttribute('width', w);
      map.setAttribute('height', h);
      map.setAttribute('href', canvas.toDataURL('image/png'));
      filter.setAttribute('width', w);
      filter.setAttribute('height', h);
      frost.setAttribute('stdDeviation', Math.min(10, Math.max(7, w * .014)));
      optics.style.filter = 'url("#' + id + '")';
    }
    function schedule() { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } }
    function copyStaticUI() {
      try {
        const page = backdrop.contentDocument;
        if (!page?.documentElement || page.URL === 'about:blank') return;
        const style = page.defaultView.getComputedStyle(page.body);
        let background = style.backgroundColor;
        let values = background.match(/[\d.]+/g)?.map(Number);
        if (!values || (values.length > 3 && values[3] < .9)) {
          background = page.defaultView.getComputedStyle(page.documentElement).backgroundColor;
          values = background.match(/[\d.]+/g)?.map(Number);
        }
        if (!values || (values.length > 3 && values[3] < .9)) {
          const ink = style.color.match(/[\d.]+/g)?.map(Number) || [240,240,240];
          values = (ink[0]+ink[1]+ink[2])/3 > 140 ? [24,24,24] : [245,245,245];
          background = 'rgb(' + values.join(',') + ')';
        }
        const light = .2126*values[0]+.7152*values[1]+.0722*values[2] > 140;
        glass.dataset.surface = light ? 'light' : 'dark';
        const surface = root.host || doc.body;
        surface.style.setProperty('--app-ui-background', background);
        const ui = doc.importNode(page.documentElement, true);
        ui.querySelectorAll('script,iframe,object,embed,meta,base').forEach(node => node.remove());
        for (const element of ui.querySelectorAll('*')) {
          for (const attribute of [...element.attributes]) if (/^on/i.test(attribute.name)) element.removeAttribute(attribute.name);
        }
        for (const style of ui.querySelectorAll('style')) style.textContent = style.textContent.replace(/:root\b/g, 'html');
        ui.inert = true;
        uiRoot.replaceChildren(ui);
        schedule();
      } catch (_) { /* The border-only lens remains available if a snapshot is not ready. */ }
    }
    backdrop.addEventListener('load', copyStaticUI);
    copyStaticUI();
    if ('ResizeObserver' in window) new ResizeObserver(schedule).observe(glass);
    addEventListener('resize', schedule, {passive: true});
    addEventListener('scroll', schedule, {passive: true, capture: true});
    root.host?.addEventListener('scroll', schedule, {passive: true});
    schedule();
  }
  
  async function readStaticUIFromCache(scopeURL) {
    if (typeof caches === 'undefined') return '';
    const marker = ':' + encodeURIComponent(scopeURL) + ':';
    const uiURL = new URL('./pwa-ui.html', scopeURL).href;
    const names = (await caches.keys()).filter(name => name.startsWith('velvitty-pwa:') && name.includes(marker) && name.endsWith(':shell')).reverse();
    for (const cacheName of names) {
      const response = await caches.match(uiURL, {cacheName});
      if (response?.ok) {
        const html = await response.text();
        if (html.trim()) return html;
      }
    }
    return '';
  }
  
  function connectionError() {
    if (document.querySelector('velvitty-pwa-connection-error')) return;
    const overlay = document.createElement('velvitty-pwa-connection-error');
    const root = overlay.attachShadow({mode: 'open'});
    root.innerHTML = "<style>:host{position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;align-items:safe center;overflow:auto;box-sizing:border-box;padding:28px;background:var(--app-ui-background,#181818);color:#fff;font:16px/1.7 system-ui,-apple-system,\"Noto Sans KR\",sans-serif;text-align:center;isolation:isolate}\n*{box-sizing:border-box}.app-backdrop{position:fixed;inset:-5px;z-index:-2;width:calc(100% + 10px);height:calc(100% + 10px);border:0;pointer-events:none;opacity:.84;filter:none;background:transparent}.scene{position:fixed;inset:0;z-index:-1;background:transparent;backdrop-filter:blur(1.3px);-webkit-backdrop-filter:blur(1.3px);pointer-events:none}\n.glass{--lens-radius:32px;position:relative;isolation:isolate;width:min(620px,100%);padding:38px 42px 34px;border:1px solid #ffffff1a;border-radius:var(--lens-radius);background:transparent;backdrop-filter:blur(8.5px);-webkit-backdrop-filter:blur(8.5px);box-shadow:0 30px 75px #0005,0 3px 0 #ffffff05,inset 0 1px 2px #ffffff30,inset 0 -3px 4px #ffffff0d;pointer-events:none;filter:none;opacity:1}.lens-clip{position:absolute;inset:0;z-index:0;border-radius:inherit;overflow:hidden;pointer-events:none}.lens-optics{position:absolute;inset:0;z-index:0;border-radius:inherit;overflow:hidden;pointer-events:none;background:transparent;filter:none}.lens-copy{position:absolute;display:block;max-width:none;margin:0;padding:0;border:0;pointer-events:none;opacity:1;background:transparent;filter:none}.glass:before{content:\"\";position:absolute;z-index:2;inset:0;padding:1px;border-radius:inherit;pointer-events:none;background:conic-gradient(from 142deg at 50% 50%,transparent 0deg,#ff9d7f88 9deg,#ffd17377 19deg,#a8edc777 29deg,#88dcff88 39deg,#aeb4ff88 49deg,#e0acff77 59deg,transparent 78deg,transparent 175deg,#e0acff66 190deg,#88dcff77 205deg,#a8edc766 217deg,#ffd17366 229deg,#ff9d7f66 241deg,transparent 260deg,transparent 360deg);-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);mask-composite:exclude}.glass:after{content:\"\";position:absolute;z-index:2;inset:-4px -3px -7px;border-radius:calc(var(--lens-radius) + 4px);border:1px solid #ffffff0d;box-shadow:inset 0 -2px 3px #ffffff0d,0 4px 7px #0002;pointer-events:none}.brand{position:relative;z-index:3;margin:0 0 28px;color:#f4f4f4;font-size:13px;font-weight:500;letter-spacing:.04em;overflow-wrap:anywhere;text-shadow:0 1px 4px #0007}.symbol{position:relative;z-index:3;display:grid;place-items:center;width:72px;height:72px;margin:0 auto 26px;border:1px solid #ffffff35;border-radius:22px;background:linear-gradient(135deg,#ffffff14,#ffffff02);box-shadow:inset 0 1px 1px #ffffff70,inset 0 -2px 2px #ffffff20,0 3px 7px #0002;color:#fff}.symbol svg{width:32px;height:32px}.primary{position:relative;z-index:3;margin:0;font-size:clamp(18px,2.8vw,23px);line-height:1.75;font-weight:600;letter-spacing:-.04em;word-break:keep-all;overflow-wrap:anywhere;text-shadow:0 1px 5px #0008}.secondary{position:relative;z-index:3;margin:20px 0 29px;color:#f1f1f1;font-size:15px;line-height:1.75;word-break:keep-all;text-shadow:0 1px 4px #0007}.retry-note{position:relative;z-index:3;margin:27px 0 0;color:#e5e5e5;font-size:12px;line-height:1.8;word-break:keep-all;letter-spacing:-.02em;text-shadow:0 1px 3px #0006}.retry-surface{position:fixed;inset:0;z-index:5;width:100%;height:100%;margin:0;padding:0;border:0;background:transparent;cursor:pointer;outline:none}.retry-surface:focus-visible~.glass{outline:3px solid #fff;outline-offset:10px}\n@media(max-width:540px){:host{padding:20px}.glass{padding:28px 23px}.brand{margin-bottom:25px}.symbol{width:64px;height:64px;margin-bottom:23px}.secondary{font-size:14px;margin-top:17px;margin-bottom:25px}}\n\n.glass{--lens-ink:#fff;--lens-muted:#ededed}.glass[data-surface=\"light\"]{--lens-ink:#171717;--lens-muted:#444}.glass :is(.brand,.primary,.symbol){color:var(--lens-ink)}.glass :is(.secondary,.retry-note){color:var(--lens-muted)}.glass[data-surface=\"light\"] :is(.brand,.primary,.secondary,.retry-note){text-shadow:none}\n</style><iframe class=\"app-backdrop\" title=\"\" sandbox=\"allow-same-origin\" tabindex=\"-1\" inert aria-hidden=\"true\"></iframe><button class=\"retry-surface\" type=\"button\" aria-label=\"연결을 다시 시도하려면 화면을 아무 곳이나 누르세요.\"></button><div class=\"scene\" aria-hidden=\"true\"></div><main class=\"glass\" role=\"alert\" aria-live=\"assertive\" aria-labelledby=\"connection-message\" aria-describedby=\"connection-guide\"><h1 class=\"brand\"></h1><div class=\"symbol\"><svg viewBox=\"0 0 32 32\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.6\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M4 11a20 20 0 0 1 5-3m6-1a20 20 0 0 1 13 4M8 16a13 13 0 0 1 5-2m6 0a13 13 0 0 1 5 2M12 21a7 7 0 0 1 8 0M16 26h.01M4 4l24 24\"/></svg></div><p class=\"primary\" id=\"connection-message\"></p><p class=\"secondary\" id=\"connection-guide\"></p><p class=\"retry-note\">연결을 다시 시도하려면 화면을 아무 곳이나 누르세요.</p></main>";
    const split = CONNECTION_MESSAGE.indexOf(' 네트워크');
    root.querySelector('.brand').textContent = document.title;
    root.querySelector('.primary').textContent = CONNECTION_MESSAGE.slice(0, split);
    root.querySelector('.secondary').textContent = CONNECTION_MESSAGE.slice(split + 1);
    root.querySelector('button').addEventListener('click', () => location.reload());
    for (const element of document.body.children) element.inert = true;
    document.body.append(overlay);
    root.querySelector('button').focus();
    installGlassLens(root);
  }
  const standalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const host = document.createElement('velvitty-pwa');
  const shadow = host.attachShadow({mode: 'open'});
  shadow.innerHTML = `<style>
    :host{position:fixed;right:max(12px,env(safe-area-inset-right));bottom:max(12px,env(safe-area-inset-bottom));z-index:10000;font:13px/1.55 system-ui,-apple-system,sans-serif;color:#f5f5f5;text-align:left;letter-spacing:normal}
    *{box-sizing:border-box}button{font:inherit;cursor:pointer}button:focus-visible,a:focus-visible{outline:3px solid #c5b5ff;outline-offset:3px}
    .open{border:1px solid #ffffff3d;border-radius:99px;padding:9px 13px;background:#222128;color:#fff;box-shadow:0 3px 16px #0002;min-height:40px}
    .panel{width:min(310px,calc(100vw - 24px));margin-bottom:8px;padding:18px;border:1px solid #ffffff38;border-radius:18px;background:#24232b;box-shadow:0 8px 40px #0004}
    [hidden]{display:none!important}h2{font-size:16px;margin:0 0 9px}p{margin:8px 0;color:#dddce5}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
    .action{border:1px solid #ffffff38;border-radius:9px;background:#eee9ff;color:#24202e;padding:8px 12px;min-height:40px}.close{background:transparent;color:#fff}.status{font-size:12px;color:#c4c1d0}
    @media print{:host{display:none}}
  </style><section class="panel" id="panel" aria-labelledby="title" hidden><h2 id="title"></h2><p id="message"></p><p class="status" id="status" role="status" aria-live="polite"></p><div class="actions"><button class="action" id="install" hidden></button><button class="action" id="update" hidden></button><button class="action close" id="close"></button></div></section><button class="open" id="open" aria-expanded="false" aria-controls="panel"></button>`;
  const $ = id => shadow.getElementById(id);
  function draw() {
    $('title').textContent = words('앱으로 사용하기', 'Use as an app');
    $('open').textContent = registration?.waiting ? words('새 버전 있음', 'Update available') : words('앱 설치', 'Install app');
    $('open').hidden = standalone() && !registration?.waiting;
    $('install').hidden = !installEvent || standalone();
    $('install').textContent = words('설치하기', 'Install');
    $('update').hidden = !registration?.waiting;
    $('update').textContent = words('저장 후 업데이트', 'Update after saving');
    $('close').textContent = words('닫기', 'Close');
    $('message').textContent = registration?.waiting
      ? words('새 버전이 준비되었습니다. 작업을 저장한 뒤 업데이트해 주세요. 화면이 새로고침됩니다.', 'A new version is ready. Save your work before updating; the page will reload.')
      : installEvent
        ? words('이 도구를 독립된 앱 창에서 열 수 있습니다.', 'Open this tool in its own app window.')
        : words('브라우저 메뉴의 앱 설치 또는 홈 화면에 추가를 이용해 주세요. iPhone·iPad에서는 공유 메뉴에서 홈 화면에 추가를 선택할 수 있습니다.', 'Use Install app or Add to Home Screen in your browser menu. On iPhone and iPad, use Share, then Add to Home Screen.');
    $('status').textContent = !navigator.onLine
      ? CONNECTION_MESSAGE
      : ready
        ? words('앱 설치 준비가 완료되었습니다. 실행하려면 인터넷 연결이 필요합니다.', 'The app is ready to install. An internet connection is required to launch it.')
        : words('앱 설치를 준비하고 있습니다.', 'Preparing app installation.');
  }
  function close() { $('panel').hidden = true; $('open').setAttribute('aria-expanded', 'false'); $('open').focus(); }
  $('open').addEventListener('click', () => { const open = $('panel').hidden; $('panel').hidden = !open; $('open').setAttribute('aria-expanded', String(open)); if(open) $('close').focus(); });
  $('close').addEventListener('click', close);
  shadow.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
  $('install').addEventListener('click', async () => {
    if (!installEvent) return;
    const event = installEvent;
    installEvent = null;
    try { await event.prompt(); await event.userChoice; } catch (_) { /* Menu installation remains available. */ }
    draw();
  });
  $('update').addEventListener('click', () => { if (registration?.waiting) { reloading = true; registration.waiting.postMessage({type: 'SKIP_WAITING'}); } });
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (reloading) { reloading = false; location.reload(); } });
  window.addEventListener('beforeinstallprompt', event => { event.preventDefault(); installEvent = event; draw(); });
  window.addEventListener('appinstalled', () => { installEvent = null; $('panel').hidden = true; draw(); });
  window.addEventListener('online', draw);
  window.addEventListener('offline', draw);
  window.addEventListener('pageshow', event => { if (event.persisted && !navigator.onLine) connectionError(); });
  new MutationObserver(draw).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
  matchMedia('(display-mode: standalone)').addEventListener?.('change', draw);
  async function start() {
    if (!navigator.onLine) { connectionError(); return; }
    if (document.querySelector('velvitty-pwa')) return;
    if (window.top === window) document.body.append(host);
    draw();
    try {
      registration = await navigator.serviceWorker.register(new URL('sw.js', base), {scope: base.href, updateViaCache: 'none'});
      draw();
      registration.addEventListener('updatefound', () => {
        const worker = registration.installing;
        worker?.addEventListener('statechange', () => { if (worker.state === 'installed') { if (!registration.waiting) ready = true; draw(); } });
      });
      const active = await navigator.serviceWorker.ready;
      if (active.scope === registration.scope) { ready = true; active.active?.postMessage({type: 'REFRESH_UI'}); draw(); }
    } catch (_) {
      $('status').textContent = words('앱 설치 준비를 마치지 못했습니다. 연결 상태에서 다시 열어 주세요.', 'App installation setup did not finish. Reopen while connected.');
    }
  }
  if (document.readyState === 'complete') start(); else window.addEventListener('load', start, {once: true});
})();
