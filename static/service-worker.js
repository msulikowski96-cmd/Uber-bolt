const CACHE = "taxi-calculator-offline-v2";
const RUNTIME = "taxi-calculator-runtime";

const PRECACHE_URLS = [
  '/',
  '/static/style.css',
  '/static/script.js',
  '/static/manifest.json',
  '/generated-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  const currentCaches = [CACHE, RUNTIME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return cacheNames.filter(cacheName => !currentCaches.includes(cacheName));
    }).then(cachesToDelete => {
      return Promise.all(cachesToDelete.map(cacheToDelete => {
        return caches.delete(cacheToDelete);
      }));
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.url.startsWith(self.location.origin)) {
    event.respondWith(
      caches.match(event.request).then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return caches.open(RUNTIME).then(cache => {
          return fetch(event.request).then(response => {
            if (event.request.method === 'GET' && response.status === 200) {
              return cache.put(event.request, response.clone()).then(() => {
                return response;
              });
            }
            return response;
          }).catch(() => {
            if (event.request.destination === 'document') {
              return caches.match('/');
            }
          });
        });
      })
    );
  }
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
