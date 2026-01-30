// Service Worker for Push Notifications
// Place this file in public/sw.js

self.addEventListener('install', (event) => {
    console.log('Service Worker installed');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker activated');
    event.waitUntil(self.clients.claim());
});

// Handle push notification
self.addEventListener('push', (event) => {
    console.log('Push notification received:', event);

    if (!event.data) {
        console.log('No data in push event');
        return;
    }

    try {
        const data = event.data.json();

        const options = {
            body: data.body || '',
            icon: data.icon || '/logo.png',
            badge: data.badge || '/badge.png',
            data: data.data || {},
            actions: data.actions || [
                {
                    action: 'open',
                    title: 'View Dashboard',
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss',
                },
            ],
            tag: data.tag || 'ai-insight',
            requireInteraction: false,
            vibrate: [200, 100, 200],
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'AI Insight', options)
        );
    } catch (error) {
        console.error('Error handling push:', error);
    }
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);

    event.notification.close();

    if (event.action === 'dismiss') {
        return;
    }

    // Open dashboard or specific insight
    const urlToOpen = event.notification.data.insight_id
        ? `/chat?insight_id=${event.notification.data.insight_id}`
        : '/dashboard';

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            // Check if there's already an open window
            for (const client of clientList) {
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }

            // Open new window
            if (self.clients.openWindow) {
                return self.clients.openWindow(urlToOpen);
            }
        })
    );
});

// Handle notification close
self.addEventListener('notificationclose', (event) => {
    console.log('Notification closed:', event);
    // Optional: Track notification dismissals
});
