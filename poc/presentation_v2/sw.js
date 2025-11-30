// Service Worker for Progressive Web App
const CACHE_NAME = 'trading-dashboard-v1';
const urlsToCache = [
  './',
  './live_demo.html',
  './per_symbol_trading/summary.json',
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js',
  'https://unpkg.com/lightweight-charts@latest/dist/lightweight-charts.standalone.production.js'
];

// Install event - cache resources
self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .catch(err => {
        console.error('[SW] Cache failed:', err);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          console.log('[SW] Serving from cache:', event.request.url);
          return response;
        }

        // Clone the request
        const fetchRequest = event.request.clone();

        return fetch(fetchRequest).then(response => {
          // Check if valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });

          return response;
        }).catch(err => {
          console.error('[SW] Fetch failed:', err);
          // Return offline page if available
          return caches.match('./live_demo.html');
        });
      })
  );
});

// Background sync for offline data
self.addEventListener('sync', event => {
  console.log('[SW] Background sync:', event.tag);
  if (event.tag === 'sync-trades') {
    event.waitUntil(syncTrades());
  }
});

async function syncTrades() {
  console.log('[SW] Syncing trades...');
  // Implementation for syncing offline trades
  try {
    const db = await openDB();
    const trades = await db.getAll('pending-trades');
    
    for (const trade of trades) {
      // Send to server
      await fetch('/api/trades', {
        method: 'POST',
        body: JSON.stringify(trade)
      });
      // Remove from pending
      await db.delete('pending-trades', trade.id);
    }
    
    console.log('[SW] Sync complete');
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

// Push notifications
self.addEventListener('push', event => {
  console.log('[SW] Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'New trading signal!',
    icon: './icon-192.png',
    badge: './badge-72.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Details',
        icon: './checkmark.png'
      },
      {
        action: 'close',
        title: 'Dismiss',
        icon: './xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Trading Dashboard', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification clicked:', event.action);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('./live_demo.html')
    );
  }
});

// IndexedDB helper
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TradingDashboardDB', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending-trades')) {
        db.createObjectStore('pending-trades', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

// Periodic background sync (if supported)
self.addEventListener('periodicsync', event => {
  if (event.tag === 'update-prices') {
    event.waitUntil(updatePrices());
  }
});

async function updatePrices() {
  console.log('[SW] Updating prices in background...');
  try {
    const response = await fetch('./per_symbol_trading/summary.json');
    const data = await response.json();
    
    const cache = await caches.open(CACHE_NAME);
    await cache.put('./per_symbol_trading/summary.json', new Response(JSON.stringify(data)));
    
    console.log('[SW] Prices updated');
  } catch (error) {
    console.error('[SW] Price update failed:', error);
  }
}

console.log('[SW] Service Worker loaded');
