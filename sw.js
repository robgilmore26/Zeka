const CACHE='zeka-v19';
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
  e.respondWith(
    caches.match(e.request).then(r=>r||fetch(e.request).then(res=>{
      if(res.ok&&e.request.method==='GET'){
        const clone=res.clone();
        caches.open(CACHE).then(c=>c.put(e.request,clone));
      }
      return res;
    })).catch(()=>caches.match('index.html'))
  );
});
