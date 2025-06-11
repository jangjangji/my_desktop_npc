from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
import os
from calendar_utils import (
    get_today_events, create_calendar_event, get_calendar_list,
    update_calendar_event, delete_calendar_event, get_event_details
)
from news_briefing import fetch_and_summarize_rss
from meeting_handler import process_meeting_notes
from models.meeting import Meeting
from config.database import SessionLocal
from datetime import datetime
import pytz

app = Flask(__name__)
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# 루트 폴더와 static 폴더 경로 설정
ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(ROOT_FOLDER, 'static')

# 서비스 워커 헤더 설정
@app.after_request
def add_header(response):
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/sw.js')
def service_worker():
    """루트 경로에 있는 서비스 워커 파일을 서빙합니다."""
    response = send_from_directory(ROOT_FOLDER, 'sw.js', mimetype='application/javascript')
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    """static 파일을 서빙합니다."""
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/')
def index():
    events = get_today_events()
    calendars = get_calendar_list()
    return render_template('index.html', events=events, calendars=calendars)

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/summarize')
def summarize():
    try:
        result = fetch_and_summarize_rss("https://feeds.feedburner.com/zdkorea", limit=5)
        return jsonify({"summary": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/calendar/list')
def calendar_list():
    try:
        calendars = get_calendar_list()
        return jsonify({"calendars": calendars})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/calendar/add', methods=['POST'])
def add_event():
    try:
        data = request.get_json()
        calendar_id = data.get('calendar_id', 'primary')  # 기본값은 기본 캘린더
        title = data.get('title')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        description = data.get('description')
        location = data.get('location')
        attendees = data.get('attendees', [])

        if not all([title, start_time, end_time]):
            return jsonify({
                'success': False,
                'error': '제목, 시작 시간, 종료 시간은 필수입니다.'
            }), 400

        result = create_calendar_event(
            calendar_id=calendar_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/calendar/event/<calendar_id>/<event_id>')
def get_event(calendar_id, event_id):
    try:
        result = get_event_details(calendar_id, event_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/calendar/update/<calendar_id>/<event_id>', methods=['PUT'])
def update_event(calendar_id, event_id):
    try:
        data = request.get_json()
        title = data.get('title')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        description = data.get('description')
        location = data.get('location')
        attendees = data.get('attendees', [])

        if not all([title, start_time, end_time]):
            return jsonify({
                'success': False,
                'error': '제목, 시작 시간, 종료 시간은 필수입니다.'
            }), 400

        result = update_calendar_event(
            calendar_id=calendar_id,
            event_id=event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/calendar/delete/<calendar_id>/<event_id>', methods=['DELETE'])
def delete_event(calendar_id, event_id):
    try:
        result = delete_calendar_event(calendar_id, event_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/calendar/today')
def get_today_events_api():
    try:
        events = get_today_events()
        if events == "오늘 일정은 없습니다.":
            return jsonify([])
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/meeting')
def meeting():
    return render_template('meeting.html')

@app.route('/process_meeting_notes', methods=['POST'])
def handle_meeting_notes():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'status': 'error',
                'message': '회의록 내용이 없습니다.'
            }), 400
            
        result = process_meeting_notes(data['text'])
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/save_meeting_notes', methods=['POST'])
def save_meeting_notes():
    try:
        data = request.get_json()
        if not data or 'original_text' not in data or 'formatted_text' not in data:
            return jsonify({
                'status': 'error',
                'message': '필수 데이터가 누락되었습니다.'
            }), 400

        # 현재 시간을 한국 시간으로 변환
        seoul_tz = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M')
        
        # 데이터베이스 세션 생성
        db = SessionLocal()
        try:
            # 회의록 생성
            meeting = Meeting(
                title=f"회의록 {current_time}",
                original_content=data['original_text'],
                summarized_content=data['formatted_text'],
                category='auto'  # 자동 저장된 회의록
            )
            
            # 데이터베이스에 저장
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            
            return jsonify({
                'status': 'success',
                'message': '회의록이 저장되었습니다.',
                'meeting_id': meeting.id
            })
            
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/meetings')
def meetings():
    # 데이터베이스 세션 생성
    db = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 9  # 한 페이지당 보여줄 회의록 수
        
        # 전체 회의록 수 조회
        total = db.query(Meeting).count()
        total_pages = (total + per_page - 1) // per_page
        
        # 회의록 목록 조회 (최신순, 페이지네이션 적용)
        meetings = db.query(Meeting).order_by(Meeting.created_at.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
            
        return render_template('meeting_list.html', 
            meetings=meetings,
            page=page,
            total_pages=total_pages,
            category="",
            tag="",
            seoul_tz=pytz.timezone('Asia/Seoul')
        )
    finally:
        db.close()

@app.route('/meetings/<int:meeting_id>')
def meeting_detail(meeting_id):
    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return render_template('404.html'), 404
        return render_template('meeting_detail.html', meeting=meeting)
    finally:
        db.close()

@app.route('/meetings/<int:meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return jsonify({
                'status': 'error',
                'message': '회의록을 찾을 수 없습니다.'
            }), 404
            
        db.delete(meeting)
        db.commit()
        
        return jsonify({
            'status': 'success',
            'message': '회의록이 삭제되었습니다.'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
