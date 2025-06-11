// Service Worker for Calendar Notifications

const CACHE_NAME = 'calendar-cache-v1';

// 서비스 워커 설치
self.addEventListener('install', (event) => {
    console.log('Service Worker 설치됨');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll([
                '/',
                '/static/js/notifications.js',
                '/static/calendar-icon.png'
            ]);
        })
    );
    self.skipWaiting();
});

// 서비스 워커 활성화
self.addEventListener('activate', (event) => {
    console.log('Service Worker 활성화됨');
    event.waitUntil(
        Promise.all([
            clients.claim(),
            // 이전 캐시 삭제
            caches.keys().then(keys => Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            ))
        ])
    );
});

// 알림 클릭 처리
self.addEventListener('notificationclick', (event) => {
    console.log('알림 클릭됨:', event.notification.title);
    
    event.notification.close();
    
    // 메인 창 열기 또는 포커스
    event.waitUntil(
        clients.matchAll({type: 'window'}).then(windowClients => {
            // 이미 열린 창이 있는지 확인
            for (let client of windowClients) {
                if (client.url === '/' && 'focus' in client) {
                    return client.focus();
                }
            }
            // 열린 창이 없으면 새 창 열기
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});

// 알림 닫기 처리
self.addEventListener('notificationclose', (event) => {
    console.log('알림 닫힘:', event.notification.title);
});

// 푸시 메시지 처리
self.addEventListener('push', (event) => {
    console.log('푸시 메시지 받음:', event.data?.text());
    
    if (!event.data) return;

    try {
        const data = event.data.json();
        
        // 알림 옵션 설정
        const options = {
            body: data.body || '일정 알림',
            icon: '/static/calendar-icon.png',
            badge: '/static/calendar-icon.png',
            requireInteraction: true,
            silent: false,
            tag: `calendar-notification-${Date.now()}`,
            vibrate: [200, 100, 200],
            data: {
                timestamp: Date.now(),
                eventId: data.eventId
            },
            actions: [
                {
                    action: 'view',
                    title: '일정 보기'
                },
                {
                    action: 'close',
                    title: '닫기'
                }
            ]
        };

        // 알림 표시
        event.waitUntil(
            self.registration.showNotification(data.title || '캘린더 알림', options)
            .then(() => {
                console.log('알림 표시 성공');
                // 클라이언트에게 알림 표시 완료 메시지 전송
                return self.clients.matchAll().then(clients => {
                    clients.forEach(client => {
                        client.postMessage({
                            type: 'NOTIFICATION_SHOWN',
                            notification: {
                                title: data.title,
                                timestamp: Date.now()
                            }
                        });
                    });
                });
            })
            .catch(error => {
                console.error('알림 표시 실패:', error);
            })
        );
    } catch (error) {
        console.error('푸시 메시지 처리 중 오류:', error);
    }
}); 