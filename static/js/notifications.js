// 시간 포맷팅 유틸리티
function formatDateTime(date) {
    return new Intl.DateTimeFormat('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    }).format(date);
}

// 테스트 알림 보내기
async function sendTestNotification() {
    try {
        if (Notification.permission === "granted") {
            const notification = new Notification("테스트 알림", {
                body: "알림 시스템이 정상적으로 작동합니다.",
                icon: '/static/calendar-icon.png',
                badge: '/static/calendar-icon.png',
                requireInteraction: true
            });

            notification.onclick = () => {
                window.focus();
                notification.close();
            };

            // 알림음 재생
            await playNotificationSound();
            console.log('테스트 알림 전송 성공');
            return true;
        }
        console.error('알림 권한이 없습니다.');
        return false;
    } catch (error) {
        console.error('테스트 알림 전송 실패:', error);
        return false;
    }
}

// 서비스 워커 등록 및 알림 초기화
async function initializeNotifications() {
    try {
        // 알림 권한 요청
        if (!("Notification" in window)) {
            console.error("이 브라우저는 알림을 지원하지 않습니다.");
            return false;
        }

        let permission = Notification.permission;
        
        if (permission === "default") {
            permission = await Notification.requestPermission();
            console.log('알림 권한 요청 결과:', permission);
        }

        if (permission !== "granted") {
            console.error("알림 권한이 거부되었습니다.");
            return false;
        }

        console.log('알림 권한 상태:', permission);

        // 서비스 워커 등록
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js', {
                    scope: '/'
                });
                console.log('서비스 워커 등록 성공:', registration.scope);

                // 서비스 워커 상태 확인
                if (registration.active) {
                    console.log('서비스 워커가 활성화되어 있습니다.');
                } else {
                    console.log('서비스 워커 활성화 대기 중...');
                    await new Promise((resolve) => {
                        registration.addEventListener('activate', () => {
                            console.log('서비스 워커가 활성화되었습니다.');
                            resolve();
                        });
                    });
                }

                // 테스트 알림 전송
                const testResult = await sendTestNotification();
                if (!testResult) {
                    console.error('테스트 알림 전송 실패');
                    return false;
                }

                return true;
            } catch (error) {
                console.error('서비스 워커 등록 실패:', error);
                return false;
            }
        }
        console.error('서비스 워커를 지원하지 않는 브라우저입니다.');
        return false;
    } catch (error) {
        console.error('알림 초기화 실패:', error);
        return false;
    }
}

// 일정 알림 예약
async function scheduleEventNotification(event) {
    const startTime = new Date(event.start_time);
    const now = new Date();
    
    // 알림 시간 계산 (시작 10분 전)
    const notificationTime = new Date(startTime.getTime() - (10 * 60 * 1000));
    
    console.log('알림 예약 시도:', {
        title: event.title,
        startTime: startTime.toLocaleString(),
        notificationTime: notificationTime.toLocaleString(),
        now: now.toLocaleString()
    });
    
    // 이미 지난 시간이면 알림을 예약하지 않음
    if (notificationTime <= now) {
        console.log('알림 시간이 이미 지났습니다:', event.title);
        return;
    }

    const timeUntilNotification = notificationTime.getTime() - now.getTime();
    console.log(`알림 예약: ${event.title}, ${Math.round(timeUntilNotification/1000/60)}분 후`);

    // 직접 알림 예약
    const directNotificationTimeout = setTimeout(async () => {
        try {
            if (Notification.permission === "granted") {
                console.log('직접 알림 표시 시도:', event.title);
                const notification = new Notification(event.title, {
                    body: `10분 후에 일정이 시작됩니다.\n시작 시간: ${formatDateTime(startTime)}`,
                    icon: '/static/calendar-icon.png',
                    badge: '/static/calendar-icon.png',
                    requireInteraction: true,
                    tag: `calendar-notification-${Date.now()}`
                });

                notification.onclick = () => {
                    window.focus();
                    notification.close();
                };

                await playNotificationSound();
                console.log('직접 알림 표시 성공:', event.title);
            }
        } catch (error) {
            console.error('직접 알림 표시 실패:', error);
        }
    }, timeUntilNotification);

    // 서비스 워커를 통한 알림 예약
    if (navigator.serviceWorker?.controller) {
        console.log('서비스 워커에 알림 예약 요청:', event.title);
        navigator.serviceWorker.controller.postMessage({
            type: 'SCHEDULE_NOTIFICATION',
            title: event.title,
            body: `10분 후에 일정이 시작됩니다.\n시작 시간: ${formatDateTime(startTime)}`,
            timestamp: notificationTime.getTime()
        });
    } else {
        console.warn('서비스 워커가 활성화되지 않았습니다.');
    }

    return directNotificationTimeout;
}

// 일정 알림 체크
async function checkUpcomingEvents() {
    try {
        console.log('일정 데이터 요청 시작');
        const response = await fetch('/calendar/today');
        if (!response.ok) {
            throw new Error('일정 조회 실패');
        }

        const events = await response.json();
        console.log('받은 일정 데이터:', events);
        
        if (!Array.isArray(events)) {
            console.warn('일정 데이터가 배열이 아닙니다:', events);
            return;
        }

        const now = new Date();
        const notifications = [];
        
        events.forEach(event => {
            const startTime = new Date(event.start_time);
            
            // 오늘 일정 중 아직 시작하지 않은 일정에 대해 알림 예약
            if (startTime > now) {
                notifications.push(scheduleEventNotification(event));
            } else {
                console.log('이미 시작된 일정:', event.title);
            }
        });

        return notifications;
    } catch (error) {
        console.error('일정 알림 체크 중 오류:', error);
        return [];
    }
}

// 알림음 재생
async function playNotificationSound() {
    try {
        const audio = new Audio('/static/notification.mp3');
        await audio.play();
        console.log('알림음 재생 성공');
    } catch (error) {
        console.error('알림음 재생 실패:', error);
    }
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', async () => {
    // 알림 시스템 초기화
    const notificationsEnabled = await initializeNotifications();
    console.log('알림 시스템 초기화 결과:', notificationsEnabled);
    
    if (notificationsEnabled) {
        // 초기 알림 체크
        const notifications = await checkUpcomingEvents();
        console.log('예약된 알림 수:', notifications.length);
        
        // 1분마다 알림 체크 갱신
        setInterval(async () => {
            const newNotifications = await checkUpcomingEvents();
            console.log('갱신된 알림 수:', newNotifications.length);
        }, 60 * 1000);
    } else {
        console.error('알림 시스템을 초기화할 수 없습니다.');
    }
}); 