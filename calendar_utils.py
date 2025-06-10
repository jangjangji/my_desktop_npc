from __future__ import print_function
import datetime
import os.path
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Google Calendar 읽기 권한
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_today_events():
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
            # ✅ 핵심: access_type=None 으로 오류 회피
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', include_granted_scopes='true')

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Calendar API 클라이언트 생성
    service = build('calendar', 'v3', credentials=creds)

    # 오늘 00:00~23:59 (UTC 기준) 일정 조회 범위 설정
    now = datetime.datetime.utcnow()
    start = datetime.datetime(now.year, now.month, now.day, 0, 0).isoformat() + 'Z'
    end = datetime.datetime(now.year, now.month, now.day, 23, 59).isoformat() + 'Z'

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
            "title": event.get("summary", "제목 없음"),
            "time": event['start'].get('dateTime', event['start'].get('date'))
        }
        for event in events
    ]

