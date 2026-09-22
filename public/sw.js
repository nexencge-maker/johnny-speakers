// Cache only a generic offline screen. Never cache account, payment, API or media data.
const CACHE='johnny-speakers-offline-v1';
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.add('/offline.html')).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('johnny-speakers-offline-')&&key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
  const url=new URL(event.request.url);
  if(event.request.method!=='GET'||event.request.mode!=='navigate'||url.origin!==self.location.origin)return;
  // Checkout and API calls always use the network directly.
  if(['/api/','/success'].some(path=>url.pathname.startsWith(path)))return;
  event.respondWith(fetch(event.request).catch(async()=>await caches.match('/offline.html')||new Response('Connect to the internet to open Johnny Speakers.',{status:503,headers:{'Content-Type':'text/plain'}})));
});
