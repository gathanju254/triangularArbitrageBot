// frontend/public/service-worker.js
/*
  Enhanced service worker:
  - Precaches core assets
  - Cache-first for static assets (with stale-while-revalidate)
  - Network-first for API calls (with cache-fallback)
  - Navigation fallback to index.html
  - Cache versioning and cleanup
  - Simple cache size/age trimming
  - skipWaiting / clients.claim and message-based skipWaiting
*/

const CACHE_VERSION = 'v2';
const PRECACHE = `precache-${CACHE_VERSION}`;
const RUNTIME_STATIC = `runtime-static-${CACHE_VERSION}`;
const RUNTIME_API = `runtime-api-${CACHE_VERSION}`;

// List of assets to precache. Add build-time assets here as needed.
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/favicon.ico',
  '/manifest.json',
  '/robots.txt',
  '/service-worker.js',
  // Add more static assets produced by your build (e.g. /assets/...)
];

// Runtime cache limits
const MAX_ENTRIES_STATIC = 100;
const MAX_ENTRIES_API = 50;
const MAX_AGE_SECONDS_API = 60 * 60 * 24; // 1 day

// Utility: timeout for fetches
const fetchWithTimeout = (request, ms = 7000) => {
  return Promise.race([
    fetch(request),
    new Promise((_, reject) => setTimeout(() => reject(new Error('network-timeout')), ms))
  ]);
};

// Utility: trim cache (simple FIFO)
const trimCache = async (cacheName, maxEntries) => {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  if (keys.length > maxEntries) {
    const removeCount = keys.length - maxEntries;
    for (let i = 0; i < removeCount; i++) {
      await cache.delete(keys[i]);
    }
  }
};

// Install: precache core assets
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(PRECACHE)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .catch(err => {
        console.error('Precache failed:', err);
      })
  );
});

// Activate: cleanup old caches
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames
        .filter(name => ![PRECACHE, RUNTIME_STATIC, RUNTIME_API].includes(name))
        .map(name => caches.delete(name))
    );
    await self.clients.claim();
  })());
});

// Message handler to allow skipWaiting from page
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Fetch handler: advanced routing with strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle same-origin requests — leave cross-origin to network
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) {
    return; // let the browser handle it
  }

  // Non-GET requests: try network then fallback to a 503 response
  if (request.method !== 'GET') {
    event.respondWith(
      fetch(request).catch(err => {
        console.warn('Non-GET network failed:', err);
        return new Response(JSON.stringify({ error: 'Network error' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Navigation requests (SPA) => Network-first with fallback to cache index.html
  if (request.mode === 'navigate' || (request.headers.get('accept') || '').includes('text/html')) {
    event.respondWith((async () => {
      try {
        const response = await fetchWithTimeout(request, 7000);
        // Update precache index.html if we get a 200
        if (response && response.ok) {
          const cache = await caches.open(PRECACHE);
          cache.put('/index.html', response.clone()).catch(() => {});
        }
        return response;
      } catch (err) {
        const cache = await caches.open(PRECACHE);
        const cached = await cache.match('/index.html');
        if (cached) return cached;
        return new Response('Offline', { status: 503, statusText: 'Offline' });
      }
    })());
    return;
  }

  // API calls: network-first, fallback to cache
  if (url.pathname.startsWith('/api/') || url.pathname.includes('/arbitrage/')) {
    event.respondWith((async () => {
      const cache = await caches.open(RUNTIME_API);
      try {
        const response = await fetchWithTimeout(request, 7000);
        if (response && response.ok) {
          cache.put(request, response.clone()).catch(() => {});
          // Trim API cache
          trimCache(RUNTIME_API, MAX_ENTRIES_API).catch(() => {});
        }
        return response;
      } catch (err) {
        const cached = await cache.match(request);
        if (cached) return cached;
        return new Response(JSON.stringify({ error: 'Network error' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    })());
    return;
  }

  // Static assets (js/css/images/fonts): cache-first with stale-while-revalidate
  if (/\.(?:js|css|png|jpg|jpeg|svg|gif|webp|woff2?|ttf|ico)$/.test(url.pathname)) {
    event.respondWith((async () => {
      const cache = await caches.open(RUNTIME_STATIC);
      const cached = await cache.match(request);
      const networkFetch = fetch(request).then(response => {
        if (response && response.ok) {
          cache.put(request, response.clone()).catch(() => {});
          trimCache(RUNTIME_STATIC, MAX_ENTRIES_STATIC).catch(() => {});
        }
        return response;
      }).catch(err => {
        // network failed
        console.debug('Static asset network failed:', url.pathname, err);
        return null;
      });

      // Serve cached if present, still trigger network to update in background
      if (cached) {
        // Kick off background update
        event.waitUntil(networkFetch);
        return cached;
      }

      // No cached -> wait for network
      const networkResponse = await networkFetch;
      if (networkResponse) return networkResponse;

      // As last resort, try precache
      const precache = await caches.open(PRECACHE);
      const fallback = await precache.match('/index.html');
      return fallback || new Response('Offline', { status: 503 });
    })());
    return;
  }

  // Default: fallback to network, then cache
  event.respondWith((async () => {
    try {
      const response = await fetch(request);
      return response;
    } catch (err) {
      const cache = await caches.open(RUNTIME_STATIC);
      const cached = await cache.match(request);
      if (cached) return cached;
      return new Response('Offline', { status: 503 });
    }
  })());
});