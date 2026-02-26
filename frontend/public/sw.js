// HealthStack Service Worker for Web Push Notifications

// Push event — received from backend via pywebpush
self.addEventListener('push', (event) => {
  let data = { title: 'HealthStack', body: '새로운 알림이 있습니다' };

  if (event.data) {
    try {
      data = event.data.json();
    } catch {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body || '',
    icon: data.icon || '/favicon.svg',
    badge: data.badge || '/favicon.svg',
    tag: data.tag || `healthstack-${Date.now()}`,
    data: data.data || {},
    vibrate: [200, 100, 200],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'HealthStack', options)
  );
});

// Notification click — open or focus the app
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const data = event.notification.data || {};
  let targetUrl = '/';

  if (data.type === 'medication_reminder') {
    targetUrl = '/?tab=home';
  } else if (data.type === 'health_news') {
    targetUrl = '/?tab=home';
  } else if (data.type === 'analysis_complete') {
    targetUrl = '/?tab=history';
  }

  if (data.url) {
    targetUrl = data.url;
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      return clients.openWindow(targetUrl);
    })
  );
});

// Handle subscription change (browser rotates push subscription)
self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil(
    self.registration.pushManager.subscribe(event.oldSubscription.options).then((newSub) => {
      const key = newSub.getKey('p256dh');
      const auth = newSub.getKey('auth');
      if (!key || !auth) return;

      return fetch('/api/v1/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: newSub.endpoint,
          p256dh: btoa(String.fromCharCode(...new Uint8Array(key))),
          auth_key: btoa(String.fromCharCode(...new Uint8Array(auth))),
        }),
      });
    })
  );
});

// Activate immediately
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});
