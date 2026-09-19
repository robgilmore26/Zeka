const CACHE='zeka-v63';
const ASSETS=[
  'index.html',
  'manifest.json',
  'icon-192.png',
  'icon-512.png'
];

self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(keys=>
    Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch',e=>{
  const url=e.request.url;
  // Never cache Firebase, Google auth, or Firestore requests
  if(url.includes('googleapis.com')||url.includes('firebaseapp.com')||
     url.includes('firestore')||url.includes('gstatic.com/firebasejs')||
     url.includes('accounts.google.com')||url.includes('firebaseinstallations')||
     url.includes('identitytoolkit')||url.includes('securetoken')||
     url.includes('gsi/client')||url.includes('gsi/status')){
    return;// Let the browser handle these normally
  }
  // Network-first for HTML pages. cache:'no-cache' revalidates with the server
  // (ETag/304) instead of trusting the browser's HTTP cache, so a fresh deploy
  // shows up on the next load without a hard refresh.
  if(e.request.mode==='navigate'||url.endsWith('.html')){
    e.respondWith(
      fetch(e.request.url,{cache:'no-cache',credentials:'same-origin'}).then(res=>{
        if(res.ok){const clone=res.clone();caches.open(CACHE).then(c=>c.put(e.request,clone));}
        return res;
      }).catch(()=>caches.match(e.request).then(r=>r||caches.match('index.html')))
    );
    return;
  }
  // Cache-first for static assets (audio, images, etc.)
  e.respondWith(
    caches.match(e.request).then(r=>r||fetch(e.request).then(res=>{
      if(res.ok&&e.request.method==='GET'&&!url.includes('chrome-extension')){
        const clone=res.clone();
        caches.open(CACHE).then(c=>c.put(e.request,clone));
      }
      return res;
    })).catch(()=>caches.match('index.html'))
  );
});
