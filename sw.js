// Service Worker for Calendar Notifications

const CACHE_NAME = 'calendar-cache-v1';

// 서비스 워커 설치
self.addEventListener('install', (event) => {
    console.log('서비스 워커가 설치되었습니다.');
    self.skipWaiting();
});

// 서비스 워커 활성화
self.addEventListener('activate', (event) => {
    console.log('서비스 워커가 활성화되었습니다.');
    event.waitUntil(clients.claim());
});

// 알림 예약 관리
const scheduledNotifications = new Map();

// 알림 클릭 처리
self.addEventListener('notificationclick', (event) => {
    console.log('알림 클릭됨:', event.notification.title);
    event.notification.close();

    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(clientList => {
            for (const client of clientList) {
                if (client.url && 'focus' in client) {
                    return client.focus();
                }
            }
            return clients.openWindow('/');
        })
    );
});

// 알림 닫기 처리
self.addEventListener('notificationclose', (event) => {
    console.log('알림 닫힘:', event.notification.title);
});

// 메시지 수신 처리
self.addEventListener('message', (event) => {
    if (event.data.type === 'SCHEDULE_NOTIFICATION') {
        const { title, body, timestamp } = event.data;
        const now = Date.now();
        const delay = Math.max(0, timestamp - now);

        console.log(`서비스 워커 알림 예약: ${title}, ${Math.round(delay/1000/60)}분 후`);

        // 기존 알림 취소
        const existingTimeout = scheduledNotifications.get(title);
        if (existingTimeout) {
            clearTimeout(existingTimeout);
            console.log('기존 알림 취소:', title);
        }

        // 새 알림 예약
        const timeoutId = setTimeout(async () => {
            try {
                console.log('알림 표시 시도:', title);
                await self.registration.showNotification(title, {
                    body: body,
                    icon: '/static/calendar-icon.png',
                    badge: '/static/calendar-icon.png',
                    requireInteraction: true,
                    vibrate: [200, 100, 200],
                    tag: `calendar-notification-${Date.now()}`
                });

                console.log('알림 표시 성공:', title);
                scheduledNotifications.delete(title);

                // 클라이언트에 알림 표시 알림
                const clients = await self.clients.matchAll();
                clients.forEach(client => {
                    client.postMessage({
                        type: 'NOTIFICATION_SHOWN',
                        notification: { title, body }
                    });
                });
            } catch (error) {
                console.error('알림 표시 실패:', error);
                // 실패 시 재시도
                setTimeout(async () => {
                    try {
                        await self.registration.showNotification(title, {
                            body: body,
                            icon: '/static/calendar-icon.png',
                            badge: '/static/calendar-icon.png',
                            requireInteraction: true,
                            vibrate: [200, 100, 200],
                            tag: `calendar-notification-retry-${Date.now()}`
                        });
                        console.log('알림 재시도 성공:', title);
                    } catch (retryError) {
                        console.error('알림 재시도 실패:', retryError);
                    }
                }, 1000);
            }
        }, delay);

        scheduledNotifications.set(title, timeoutId);
    }
}); 