/**
 * Service Worker for Text-to-Dataset Platform PWA
 * Handles offline functionality, background sync, and push notifications
 */

const CACHE_NAME = 'text-dataset-v1.0.0';
const OFFLINE_URL = '/offline.html';
const API_CACHE_NAME = 'api-cache-v1';

// Files to cache for offline functionality
const STATIC_RESOURCES = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/offline.html',
  '/manifest.json',
  '/logo192.png',
  '/logo512.png'
];

// API endpoints to cache
const CACHEABLE_API_PATTERNS = [
  /\/api\/users\/profile/,
  /\/api\/documents\/list/,
  /\/api\/analytics\/dashboard/,
  /\/api\/projects/
];

// Install event - cache static resources
self.addEventListener('install', event => {
  console.log('Service Worker: Install Event');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching static resources');
        return cache.addAll(STATIC_RESOURCES);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activate Event');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - handle network requests with caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle different request types with appropriate strategies
  if (request.method === 'GET') {
    if (url.pathname.startsWith('/api/')) {
      // API requests - cache-first for specific endpoints, network-first for others
      event.respondWith(handleAPIRequest(request));
    } else if (request.destination === 'document') {
      // HTML documents - network-first with offline fallback
      event.respondWith(handleDocumentRequest(request));
    } else {
      // Static resources - cache-first
      event.respondWith(handleStaticRequest(request));
    }
  } else if (request.method === 'POST') {
    // Handle POST requests with background sync
    event.respondWith(handlePostRequest(request));
  }
});

// Handle API requests
async function handleAPIRequest(request) {
  const url = new URL(request.url);
  const shouldCache = CACHEABLE_API_PATTERNS.some(pattern => pattern.test(url.pathname));

  if (shouldCache) {
    // Cache-first strategy for cacheable APIs
    try {
      const cachedResponse = await caches.match(request, { cacheName: API_CACHE_NAME });
      if (cachedResponse) {
        // Return cached response and update cache in background
        updateCacheInBackground(request);
        return cachedResponse;
      }
    } catch (error) {
      console.log('Cache lookup failed:', error);
    }

    try {
      const networkResponse = await fetch(request);
      if (networkResponse.ok) {
        const cache = await caches.open(API_CACHE_NAME);
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    } catch (error) {
      return new Response(
        JSON.stringify({ error: 'Network unavailable', offline: true }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  } else {
    // Network-first for non-cacheable APIs
    try {
      return await fetch(request);
    } catch (error) {
      return new Response(
        JSON.stringify({ error: 'Network unavailable' }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  }
}

// Handle document requests
async function handleDocumentRequest(request) {
  try {
    return await fetch(request);
  } catch (error) {
    // Return offline page if available
    const offlineResponse = await caches.match(OFFLINE_URL);
    return offlineResponse || new Response('Offline', { status: 503 });
  }
}

// Handle static resource requests
async function handleStaticRequest(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    return cachedResponse || new Response('Resource unavailable', { status: 503 });
  }
}

// Handle POST requests with background sync
async function handlePostRequest(request) {
  try {
    return await fetch(request);
  } catch (error) {
    // Store request for background sync
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      await storeFailedRequest(request);
      return new Response(
        JSON.stringify({ 
          success: true, 
          message: 'Request queued for background sync',
          queued: true 
        }),
        { 
          status: 202,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    } else {
      throw error;
    }
  }
}

// Update cache in background
async function updateCacheInBackground(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
  } catch (error) {
    console.log('Background cache update failed:', error);
  }
}

// Store failed request for background sync
async function storeFailedRequest(request) {
  const requestData = {
    url: request.url,
    method: request.method,
    headers: Object.fromEntries(request.headers.entries()),
    body: await request.text(),
    timestamp: Date.now()
  };

  // Store in IndexedDB
  const db = await openDB();
  const tx = db.transaction(['failedRequests'], 'readwrite');
  const store = tx.objectStore('failedRequests');
  await store.add(requestData);
}

// Background sync event - retry failed requests
self.addEventListener('sync', event => {
  console.log('Service Worker: Background Sync Event:', event.tag);
  
  if (event.tag === 'retry-failed-requests') {
    event.waitUntil(retryFailedRequests());
  }
});

// Retry failed requests
async function retryFailedRequests() {
  const db = await openDB();
  const tx = db.transaction(['failedRequests'], 'readwrite');
  const store = tx.objectStore('failedRequests');
  const failedRequests = await store.getAll();

  for (const requestData of failedRequests) {
    try {
      const request = new Request(requestData.url, {
        method: requestData.method,
        headers: requestData.headers,
        body: requestData.body
      });

      const response = await fetch(request);
      if (response.ok) {
        await store.delete(requestData.id);
        console.log('Retry successful for:', requestData.url);
      }
    } catch (error) {
      console.log('Retry failed for:', requestData.url, error);
    }
  }
}

// Push notification event
self.addEventListener('push', event => {
  console.log('Service Worker: Push Event');
  
  let notificationData = {
    title: 'Text Dataset Platform',
    body: 'You have a new notification',
    icon: '/logo192.png',
    badge: '/badge-72x72.png',
    tag: 'default',
    actions: [
      { action: 'view', title: 'View' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  };

  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = { ...notificationData, ...data };
    } catch (error) {
      console.error('Failed to parse push data:', error);
    }
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      tag: notificationData.tag,
      actions: notificationData.actions,
      requireInteraction: true,
      data: notificationData.data
    })
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification Click Event');
  
  event.notification.close();

  if (event.action === 'view' || !event.action) {
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then(clientList => {
          const url = event.notification.data?.url || '/dashboard';
          
          // Focus existing tab if available
          for (const client of clientList) {
            if (client.url.includes(url) && 'focus' in client) {
              return client.focus();
            }
          }
          
          // Open new tab
          if (clients.openWindow) {
            return clients.openWindow(url);
          }
        })
    );
  }
});

// Message event for communication with main thread
self.addEventListener('message', event => {
  console.log('Service Worker: Message Event:', event.data);
  
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data?.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(CACHE_NAME)
        .then(cache => cache.addAll(event.data.urls))
    );
  }
});

// IndexedDB helper functions
async function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TextDatasetPWA', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('failedRequests')) {
        const store = db.createObjectStore('failedRequests', { keyPath: 'id', autoIncrement: true });
        store.createIndex('timestamp', 'timestamp');
      }
    };
  });
}

// Periodic background sync for data updates
self.addEventListener('periodicsync', event => {
  console.log('Service Worker: Periodic Sync Event:', event.tag);
  
  if (event.tag === 'update-dashboard-data') {
    event.waitUntil(updateDashboardData());
  }
});

// Update dashboard data in background
async function updateDashboardData() {
  try {
    const response = await fetch('/api/analytics/dashboard');
    if (response.ok) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put('/api/analytics/dashboard', response.clone());
    }
  } catch (error) {
    console.log('Background dashboard update failed:', error);
  }
}

console.log('Service Worker: Loaded successfully');