from __future__ import print_function
import datetime
import os.path
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Google Calendar 읽기/쓰기 권한
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar'
]

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

    # 오늘 00:00~23:59 (UTC 기준) 일정 조회 범위 설정
    now = datetime.datetime.utcnow()
    start = datetime.datetime(now.year, now.month, now.day, 0, 0).isoformat() + 'Z'
    end = datetime.datetime(now.year, now.month, now.day, 23, 59).isoformat() + 'Z'

    # 캘린더 목록 가져오기
    calendar_colors = {}
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list.get('items', []):
        calendar_colors[calendar['id']] = {
            'backgroundColor': calendar.get('backgroundColor', '#039BE5'),
            'summary': calendar.get('summary', '기본 캘린더')
        }

    # 일정 요청
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        return "오늘 일정은 없습니다."

    return [
        {
            "id": event['id'],
            "title": event.get("summary", "제목 없음"),
            "start_time": event['start'].get('dateTime', event['start'].get('date')),
            "end_time": event['end'].get('dateTime', event['end'].get('date')),
            "description": event.get("description", ""),
            "calendar_id": event.get("organizer", {}).get("email", "primary"),
            "calendar_name": calendar_colors.get(event.get("organizer", {}).get("email", "primary"), {}).get("summary", "기본 캘린더"),
            "color": calendar_colors.get(event.get("organizer", {}).get("email", "primary"), {}).get("backgroundColor", "#039BE5")
        }
        for event in events
    ]

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

def create_calendar_event(calendar_id, title, start_time, end_time, description=None, attendees=None, location=None):
    """지정된 캘린더에 새 일정을 추가합니다.
    
    Args:
        calendar_id (str): 캘린더 ID
        title (str): 일정 제목
        start_time (str): 시작 시간 (ISO 형식: YYYY-MM-DDTHH:MM:SS)
        end_time (str): 종료 시간 (ISO 형식: YYYY-MM-DDTHH:MM:SS)
        description (str, optional): 일정 설명
        attendees (list, optional): 참석자 이메일 목록
        location (str, optional): 장소
    
    Returns:
        dict: 생성된 일정 정보
    """
    service = get_calendar_service()
    
    event = {
        'summary': title,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Seoul',
        },
    }
    
    if description:
        event['description'] = description
    
    if location:
        event['location'] = location
    
    if attendees:
        event['attendees'] = [{'email': email} for email in attendees]
        event['guestsCanModify'] = True  # 참석자가 일정을 수정할 수 있도록 설정
    
    try:
        event = service.events().insert(calendarId=calendar_id, body=event, sendUpdates='all').execute()
        return {
            'success': True,
            'id': event['id'],
            'title': event['summary'],
            'start': event['start']['dateTime'],
            'end': event['end']['dateTime'],
            'calendar_id': calendar_id
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def update_calendar_event(calendar_id, event_id, title=None, start_time=None, end_time=None, description=None, attendees=None, location=None):
    """기존 일정을 수정합니다.
    
    Args:
        calendar_id (str): 캘린더 ID
        event_id (str): 수정할 일정 ID
        title (str, optional): 수정할 일정 제목
        start_time (str, optional): 수정할 시작 시간 (ISO 형식)
        end_time (str, optional): 수정할 종료 시간 (ISO 형식)
        description (str, optional): 수정할 일정 설명
        attendees (list, optional): 수정할 참석자 이메일 목록
        location (str, optional): 수정할 장소
    
    Returns:
        dict: 수정된 일정 정보
    """
    service = get_calendar_service()
    
    try:
        # 기존 일정 정보 가져오기
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        
        # 수정할 필드만 업데이트
        if title:
            event['summary'] = title
        if start_time:
            event['start']['dateTime'] = start_time
        if end_time:
            event['end']['dateTime'] = end_time
        if description is not None:  # 빈 문자열도 허용
            event['description'] = description
        if location is not None:
            event['location'] = location
        if attendees is not None:
            event['attendees'] = [{'email': email} for email in attendees]
        
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
            sendUpdates='all'
        ).execute()
        
        return {
            'success': True,
            'id': updated_event['id'],
            'title': updated_event['summary'],
            'start': updated_event['start']['dateTime'],
            'end': updated_event['end']['dateTime']
        }
    except Exception as e:
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
    """특정 일정의 상세 정보를 가져옵니다.
    
    Args:
        calendar_id (str): 캘린더 ID
        event_id (str): 일정 ID
    
    Returns:
        dict: 일정 상세 정보
    """
    service = get_calendar_service()
    
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return {
            'success': True,
            'id': event['id'],
            'title': event.get('summary', ''),
            'start': event['start'].get('dateTime', event['start'].get('date')),
            'end': event['end'].get('dateTime', event['end'].get('date')),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'attendees': [attendee['email'] for attendee in event.get('attendees', [])]
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

