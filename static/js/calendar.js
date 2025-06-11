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

// datetime-local 입력을 위한 포맷
function formatToDateTimeLocal(date) {
    return date.toISOString().slice(0, 16);
}

// 일정 목록 새로고침
async function refreshEvents() {
    const eventsContainer = document.getElementById('events-container');
    // events-container가 없으면 (다른 페이지인 경우) 함수 실행을 중단
    if (!eventsContainer) {
        return;
    }

    try {
        const response = await fetch('/calendar/today');
        if (!response.ok) {
            throw new Error('일정 조회 실패');
        }

        const data = await response.json();
        
        if (Array.isArray(data) && data.length > 0) {
            const eventsHtml = data.map(event => `
                <div class="col-12 event-item" data-event-id="${event.id}">
                    <div class="card" style="border-left: 5px solid ${event.color};">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h5 class="card-title mb-0">${event.title}</h5>
                                <div>
                                    <span class="badge" style="background-color: ${event.color}">
                                        ${event.calendar_name}
                                    </span>
                                    <button class="btn btn-sm btn-outline-primary ms-2" 
                                            onclick="editEvent('${event.calendar_id}', '${event.id}')">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger ms-1" 
                                            onclick="deleteEvent('${event.calendar_id}', '${event.id}')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                            <p class="card-text">
                                <i class="far fa-clock me-2"></i>
                                <span class="event-time">
                                    시작: ${formatDateTime(new Date(event.start_time))}<br>
                                    종료: ${formatDateTime(new Date(event.end_time))}
                                </span>
                            </p>
                            ${event.description ? `
                            <p class="card-text text-muted">
                                <small>${event.description}</small>
                            </p>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
            
            eventsContainer.innerHTML = eventsHtml;
        } else {
            eventsContainer.innerHTML = `
                <div class="col-12">
                    <div class="card">
                        <div class="card-body text-center">
                            <i class="far fa-calendar-check fa-3x mb-3 text-muted"></i>
                            <p class="card-text">오늘은 예정된 일정이 없습니다.</p>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('일정 목록 새로고침 실패:', error);
    }
}

// 일정 삭제
async function deleteEvent(calendarId, eventId) {
    if (!confirm('정말로 이 일정을 삭제하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch(`/calendar/delete/${calendarId}/${eventId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.success) {
            await refreshEvents();
        } else {
            throw new Error(data.error || '일정 삭제 실패');
        }
    } catch (error) {
        console.error('일정 삭제 중 오류:', error);
        alert('일정 삭제 중 오류가 발생했습니다: ' + error.message);
    }
}

// 일정 수정 모달 열기
async function editEvent(calendarId, eventId) {
    try {
        const response = await fetch(`/calendar/event/${calendarId}/${eventId}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '일정 정보를 가져오는데 실패했습니다.');
        }

        // 모달 필드 설정
        document.getElementById('editEventId').value = eventId;
        document.getElementById('editCalendarId').value = calendarId;
        document.getElementById('editEventTitle').value = data.title;
        
        // 시간 설정
        const startDate = new Date(data.start);
        const endDate = new Date(data.end);
        document.getElementById('editEventStart').value = formatToDateTimeLocal(startDate);
        document.getElementById('editEventEnd').value = formatToDateTimeLocal(endDate);
        
        // 기타 필드 설정
        document.getElementById('editEventLocation').value = data.location || '';
        document.getElementById('editEventDescription').value = data.description || '';
        document.getElementById('editEventReminder').value = data.reminder_minutes || '10';
        document.getElementById('editEventAttendees').value = data.attendees ? data.attendees.join(', ') : '';
        
        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('editEventModal'));
        modal.show();
    } catch (error) {
        console.error('일정 수정 모달 열기 실패:', error);
        alert('일정 정보를 가져오는 중 오류가 발생했습니다: ' + error.message);
    }
}

// 일정 수정 저장
async function updateEvent() {
    const eventId = document.getElementById('editEventId').value;
    const calendarId = document.getElementById('editCalendarId').value;
    const title = document.getElementById('editEventTitle').value;
    const start = new Date(document.getElementById('editEventStart').value);
    const end = new Date(document.getElementById('editEventEnd').value);
    const location = document.getElementById('editEventLocation').value;
    const description = document.getElementById('editEventDescription').value;
    const reminderMinutes = parseInt(document.getElementById('editEventReminder').value);
    const attendeesInput = document.getElementById('editEventAttendees').value;
    const attendees = attendeesInput ? attendeesInput.split(',').map(email => email.trim()) : [];

    if (!title || !start || !end) {
        alert('제목, 시작 시간, 종료 시간은 필수입니다.');
        return;
    }

    try {
        const response = await fetch(`/calendar/update/${calendarId}/${eventId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title,
                start_time: start.toISOString(),
                end_time: end.toISOString(),
                location,
                description,
                reminder_minutes: reminderMinutes,
                attendees
            })
        });

        const data = await response.json();
        if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editEventModal'));
            modal.hide();
            await refreshEvents();
        } else {
            throw new Error(data.error || '일정 수정 실패');
        }
    } catch (error) {
        console.error('일정 수정 중 오류:', error);
        alert('일정 수정 중 오류가 발생했습니다: ' + error.message);
    }
}

// 새 일정 추가
async function addEvent() {
    const calendarId = document.getElementById('calendarSelect').value;
    const title = document.getElementById('eventTitle').value;
    const start = new Date(document.getElementById('eventStart').value);
    const end = new Date(document.getElementById('eventEnd').value);
    const location = document.getElementById('eventLocation').value;
    const description = document.getElementById('eventDescription').value;
    const reminderMinutes = parseInt(document.getElementById('eventReminder').value);
    const attendeesInput = document.getElementById('eventAttendees').value;
    const attendees = attendeesInput ? attendeesInput.split(',').map(email => email.trim()) : [];

    if (!title || !start || !end) {
        alert('제목, 시작 시간, 종료 시간은 필수입니다.');
        return;
    }

    try {
        const response = await fetch('/calendar/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                calendar_id: calendarId,
                title,
                start_time: start.toISOString(),
                end_time: end.toISOString(),
                location,
                description,
                reminder_minutes: reminderMinutes,
                attendees
            })
        });

        const data = await response.json();
        if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addEventModal'));
            modal.hide();
            await refreshEvents();
        } else {
            throw new Error(data.error || '일정 추가 실패');
        }
    } catch (error) {
        console.error('일정 추가 중 오류:', error);
        alert('일정 추가 중 오류가 발생했습니다: ' + error.message);
    }
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    // 현재 날짜 표시
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
    });

    // 일정 목록 로드
    refreshEvents();
}); 