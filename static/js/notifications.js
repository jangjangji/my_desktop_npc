// 시간 포맷팅 유틸리티
function formatDateTime(date) {
    return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    }).replace('AM', '오전').replace('PM', '오후');
}

// 서비스 워커 등록
async function registerServiceWorker() {
    try {
        if ('serviceWorker' in navigator) {
            const registration = await navigator.serviceWorker.register('/sw.js', {
                scope: '/'
            });
            console.log('서비스 워커 등록 성공:', registration.scope);
            
            // 서비스 워커 상태 확인
            if (registration.active) {
                console.log('서비스 워커가 이미 활성화되어 있습니다.');
            } else {
                console.log('서비스 워커 활성화 대기 중...');
                await new Promise(resolve => {
                    registration.addEventListener('activate', () => {
                        console.log('서비스 워커가 활성화되었습니다.');
                        resolve();
                    });
                });
            }
            
            // 서비스 워커 메시지 수신 처리
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data.type === 'NOTIFICATION_SHOWN') {
                    console.log('알림이 표시됨:', event.data.notification);
                    refreshEvents();
                }
            });
            
            return registration;
        }
        throw new Error('서비스 워커를 지원하지 않는 브라우저입니다.');
    } catch (error) {
        console.error('서비스 워커 등록 실패:', error);
        return null;
    }
}

// 알림 권한 요청
async function requestNotificationPermission() {
    try {
        if (!('Notification' in window)) {
            throw new Error('이 브라우저는 알림을 지원하지 않습니다.');
        }

        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            throw new Error('알림 권한이 거부되었습니다.');
        }

        console.log('알림 권한이 허용되었습니다.');
        return true;
    } catch (error) {
        console.error('알림 권한 요청 실패:', error);
        alert('알림 기능을 사용하려면 알림 권한을 허용해주세요.');
        return false;
    }
}

// 모달 알림 표시
function showNotificationModal(title, message) {
    const modal = document.getElementById('notificationModal');
    const overlay = document.getElementById('notificationOverlay');
    const messageElement = document.getElementById('notificationMessage');
    
    // 모달 요소가 없으면 (다른 페이지인 경우) 함수 실행을 중단
    if (!modal || !overlay || !messageElement) {
        return;
    }

    const modalTitle = modal.querySelector('.modal-title');
    modalTitle.textContent = title;
    messageElement.textContent = message;
    
    modal.classList.add('show');
    overlay.classList.add('show');
    
    // 알림음 재생
    playNotificationSound();
}

// 모달 알림 닫기
function closeNotificationModal() {
    const modal = document.getElementById('notificationModal');
    const overlay = document.getElementById('notificationOverlay');
    
    // 모달 요소가 없으면 (다른 페이지인 경우) 함수 실행을 중단
    if (!modal || !overlay) {
        return;
    }
    
    modal.classList.remove('show');
    overlay.classList.remove('show');
}

// 알림음 재생
function playNotificationSound() {
    const audio = new Audio('/static/notification.mp3');
    audio.play().catch(error => {
        console.log('알림음 재생 실패:', error);
    });
}

// 캘린더 열기
function openCalendar() {
    closeNotificationModal();
    window.location.reload();
}

// 알림 예약
async function scheduleNotification(title, body, timestamp) {
    try {
        const registration = await navigator.serviceWorker.ready;
        if (!registration.active) {
            throw new Error('서비스 워커가 활성화되지 않았습니다.');
        }

        // 알림 권한 다시 확인
        if (Notification.permission !== 'granted') {
            const permitted = await requestNotificationPermission();
            if (!permitted) {
                throw new Error('알림 권한이 없습니다.');
            }
        }

        // 서비스 워커에 알림 예약 메시지 전송
        registration.active.postMessage({
            type: 'SCHEDULE_NOTIFICATION',
            title,
            body,
            timestamp
        });

        // 모달 알림도 표시
        const delay = timestamp - Date.now();
        if (delay > 0) {
            setTimeout(() => {
                showNotificationModal(title, body);
            }, delay);
        }

        return true;
    } catch (error) {
        console.error('알림 예약 실패:', error);
        return false;
    }
}

// 일정 알림 체크
async function checkUpcomingEvents() {
    try {
        // 서비스 워커와 알림 권한 확인
        const registration = await navigator.serviceWorker.ready;
        if (!registration.active) {
            console.warn('서비스 워커가 아직 활성화되지 않았습니다.');
            return;
        }

        if (Notification.permission !== 'granted') {
            console.warn('알림 권한이 없습니다.');
            return;
        }

        const response = await fetch('/calendar/today');
        if (!response.ok) {
            throw new Error('일정 조회 실패');
        }

        const events = await response.json();
        if (!Array.isArray(events)) {
            console.warn('일정 데이터가 배열이 아닙니다:', events);
            return;
        }

        console.log('일정 확인 중...', new Date().toISOString());
        
        const now = new Date();
        for (const event of events) {
            const startTime = new Date(event.start_time);
            const reminderMinutes = event.reminder_minutes || 10; // 기본값 10분
            const reminderTime = new Date(startTime.getTime() - (reminderMinutes * 60000));
            
            // 알림 시간이 현재 시간보다 미래이고, 30분 이내에 알림이 예정된 경우
            const timeUntilReminder = reminderTime.getTime() - now.getTime();
            if (timeUntilReminder > 0 && timeUntilReminder <= 1800000) { // 30분 = 1800000ms
                const timeUntilStart = Math.round((startTime - now) / 60000);
                const message = `${timeUntilStart}분 후에 일정이 시작됩니다.\n시작 시간: ${formatDateTime(startTime)}`;
                
                await scheduleNotification(
                    event.title,
                    message,
                    reminderTime.getTime()
                );
            }
        }
    } catch (error) {
        console.error('일정 알림 체크 중 오류:', error);
    }
}

// 일정 목록 새로고침
async function refreshEvents() {
    try {
        const response = await fetch('/calendar/today');
        if (!response.ok) {
            throw new Error('일정 조회 실패');
        }
        
        const events = await response.json();
        
        // DOM 업데이트
        const eventList = document.querySelector('.event-list');
        if (eventList) {
            window.location.reload();
        }
    } catch (error) {
        console.error('일정 새로고침 실패:', error);
    }
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', async function() {
    try {
        console.log('알림 시스템 초기화 중...');
        
        // 서비스 워커 등록
        const registration = await registerServiceWorker();
        if (!registration) {
            console.error('서비스 워커 등록 실패');
            return;
        }
        
        // 알림 권한 확인
        const hasPermission = await requestNotificationPermission();
        if (!hasPermission) {
            console.warn('알림 권한이 없습니다.');
            return;
        }
        
        console.log('알림 시스템 초기화 완료');
        
        // 즉시 한 번 체크
        await checkUpcomingEvents();
        
        // 30분마다 알림 체크 및 일정 새로고침
        setInterval(async () => {
            await checkUpcomingEvents();
            await refreshEvents();
        }, 1800000); // 30분 = 1800000ms
    } catch (error) {
        console.error('알림 시스템 초기화 중 오류:', error);
    }
}); 