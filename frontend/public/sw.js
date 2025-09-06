// Donna Service Worker for Push Notifications
const CACHE_NAME = 'donna-v1';

// Install event
self.addEventListener('install', (event) => {
  console.log('Donna Service Worker installed');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Donna Service Worker activated');
  event.waitUntil(self.clients.claim());
});

// Push event - Handle incoming notifications
self.addEventListener('push', (event) => {
  console.log('Push received:', event);
  
  let notificationData = {};
  
  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (e) {
      notificationData = {
        title: 'Donna',
        body: event.data.text() || 'You have a new notification',
        icon: '/favicon.ico',
        badge: '/favicon.ico'
      };
    }
  }

  const options = {
    body: notificationData.body || 'You have a new notification',
    icon: notificationData.icon || '/favicon.ico',
    badge: notificationData.badge || '/favicon.ico',
    data: {
      url: notificationData.url || '/',
      type: notificationData.type || 'general'
    },
    actions: [
      {
        action: 'open',
        title: 'Open Donna'
      }
    ],
    requireInteraction: true,
    silent: false
  };

  event.waitUntil(
    self.registration.showNotification(notificationData.title || 'Donna', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clients) => {
        // Check if Donna is already open
        for (const client of clients) {
          if (client.url.includes(self.location.origin)) {
            return client.focus();
          }
        }
        // Open new window if not already open
        return self.clients.openWindow(urlToOpen);
      })
  );
});

// Background sync for offline notifications
self.addEventListener('sync', (event) => {
  if (event.tag === 'donna-notification-sync') {
    event.waitUntil(syncNotifications());
  }
});

async function syncNotifications() {
  // Handle offline notification sync if needed
  console.log('Syncing notifications...');
}