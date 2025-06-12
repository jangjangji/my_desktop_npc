from __future__ import print_function
from datetime import datetime, timezone, timedelta
import os.path
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pytz

# Google Calendar 읽기/쓰기 권한
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar'
]

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_calendar_service():
    creds = None

    # 인증된 토큰 캐시 확인
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 인증 없거나 만료 시 재인증
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', include_granted_scopes='true')

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def get_today_events():
    service = get_calendar_service()

    # 오늘 00:00~23:59 (KST 기준) 일정 조회 범위 설정
    now = datetime.now(KST)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # UTC로 변환
    start = start.astimezone(pytz.UTC)
    end = end.astimezone(pytz.UTC)

    # 캘린더 목록 가져오기
    calendar_colors = {}
    calendar_list = service.calendarList().list().execute()
    
    formatted_events = []
    
    # 각 캘린더별로 일정 조회
    for calendar in calendar_list.get('items', []):
        calendar_id = calendar['id']
        calendar_colors[calendar_id] = {
            'backgroundColor': calendar.get('backgroundColor', '#039BE5'),
            'summary': calendar.get('summary', '기본 캘린더')
        }
        
        # 일정 요청
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        def format_event_time(time_str):
            if not time_str:
                return None
            # UTC 시간을 KST로 변환
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            dt_kst = dt.astimezone(KST)
            return dt_kst.isoformat()

        for event in events:
            # 알림 설정 가져오기
            reminder_minutes = 10  # 기본값
            if 'reminders' in event:
                if not event['reminders'].get('useDefault', True):
                    overrides = event['reminders'].get('overrides', [])
                    if overrides:
                        # 팝업 알림 설정 찾기
                        for override in overrides:
                            if override.get('method') == 'popup':
                                reminder_minutes = override.get('minutes', 10)
                                break
                # 기본 알림 설정 사용
                else:
                    reminder_minutes = 10

            formatted_event = {
                "id": event['id'],
                "title": event.get("summary", "제목 없음"),
                "start_time": format_event_time(event['start'].get('dateTime', event['start'].get('date'))),
                "end_time": format_event_time(event['end'].get('dateTime', event['end'].get('date'))),
                "description": event.get("description", ""),
                "calendar_id": calendar_id,
                "calendar_name": calendar_colors[calendar_id]["summary"],
                "color": calendar_colors[calendar_id]["backgroundColor"],
                "reminder_minutes": reminder_minutes
            }
            formatted_events.append(formatted_event)

    if not formatted_events:
        return "오늘 일정은 없습니다."

    return formatted_events

def get_calendar_list():
    """사용 가능한 모든 캘린더 목록을 가져옵니다."""
    service = get_calendar_service()
    
    try:
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        return [
            {
                'id': calendar['id'],
                'summary': calendar['summary'],
                'description': calendar.get('description', ''),
                'backgroundColor': calendar.get('backgroundColor', '#039BE5'),
                'accessRole': calendar['accessRole']
            }
            for calendar in calendars
            if calendar['accessRole'] in ['owner', 'writer']  # 쓰기 권한이 있는 캘린더만 반환
        ]
    except Exception as e:
        print(f"캘린더 목록 가져오기 실패: {str(e)}")
        return []

def create_calendar_event(calendar_id='primary', title=None, start_time=None, end_time=None, 
                        description=None, location=None, attendees=None, reminder_minutes=10):
    """캘린더에 새 일정을 추가합니다."""
    try:
        service = get_calendar_service()
        
        # 시간 문자열이 ISO 형식인지 확인하고 처리
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
        # 시간이 과거인 경우 현재 시간 + 1분으로 조정
        now = datetime.now(timezone.utc)
        if start_time < now:
            start_time = now + timedelta(minutes=1)
            end_time = start_time + timedelta(minutes=30)
            
        # 종료 시간이 시작 시간보다 이전인 경우 수정
        if end_time <= start_time:
            end_time = start_time + timedelta(minutes=30)

        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Seoul'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Seoul'
            }
        }

        if location:
            event['location'] = location

        if attendees:
            event['attendees'] = [{'email': attendee} for attendee in attendees]

        # 알림 설정 (팝업과 이메일 모두 설정)
        event['reminders'] = {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': reminder_minutes},
                {'method': 'email', 'minutes': reminder_minutes}
            ]
        }

        print('일정 생성 요청:', event)  # 디버깅용 로그

        event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'  # 이메일 알림 보내기
        ).execute()

        return {
            'success': True,
            'id': event['id'],
            'htmlLink': event['htmlLink']
        }

    except Exception as e:
        print('일정 생성 중 오류:', str(e))  # 디버깅용 로그
        return {
            'success': False,
            'error': str(e)
        }

def update_calendar_event(calendar_id, event_id, title=None, start_time=None, end_time=None, description=None, attendees=None, location=None, reminder_minutes=None):
    service = get_calendar_service()
    
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if not start_dt.tzinfo:
                start_dt = KST.localize(start_dt)
            event['start'] = {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Asia/Seoul'
            }
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            if not end_dt.tzinfo:
                end_dt = KST.localize(end_dt)
            event['end'] = {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Asia/Seoul'
            }
        
        if title:
            event['summary'] = title
        if description is not None:
            event['description'] = description
        if location is not None:
            event['location'] = location
        if attendees is not None:
            event['attendees'] = [{'email': email} for email in attendees]
        if reminder_minutes is not None:
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': int(reminder_minutes)},
                    {'method': 'email', 'minutes': int(reminder_minutes)}
                ]
            }
        
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        print(f"수정된 이벤트 시간: 시작={updated_event['start']['dateTime']}, 종료={updated_event['end']['dateTime']}")
        
        return {
            'success': True,
            'id': updated_event['id'],
            'title': updated_event['summary'],
            'start': updated_event['start']['dateTime'],
            'end': updated_event['end']['dateTime'],
            'reminder_minutes': reminder_minutes if reminder_minutes is not None else None
        }
    except Exception as e:
        print(f"일정 수정 중 오류: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def delete_calendar_event(calendar_id, event_id):
    """일정을 삭제합니다.
    
    Args:
        calendar_id (str): 캘린더 ID
        event_id (str): 삭제할 일정 ID
    
    Returns:
        dict: 삭제 결과
    """
    service = get_calendar_service()
    
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id, sendUpdates='all').execute()
        return {
            'success': True,
            'message': '일정이 성공적으로 삭제되었습니다.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_event_details(calendar_id, event_id):
    """특정 일정의 상세 정보를 가져옵니다."""
    service = get_calendar_service()
    
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        # 시간 정보를 KST로 변환
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        end_time = event['end'].get('dateTime', event['end'].get('date'))
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00')).astimezone(KST)
            start_time = start_dt.isoformat()
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')).astimezone(KST)
            end_time = end_dt.isoformat()
            
        return {
            'success': True,
            'id': event['id'],
            'title': event.get('summary', ''),
            'start': start_time,
            'end': end_time,
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'attendees': [attendee['email'] for attendee in event.get('attendees', [])],
            'reminder_minutes': event.get('reminders', {}).get('overrides', [{}])[0].get('minutes', 10)
        }
    except Exception as e:
        print(f"일정 상세 정보 조회 중 오류: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

