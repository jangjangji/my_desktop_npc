from flask import Flask, render_template, jsonify, request
from calendar_utils import (
    get_today_events, create_calendar_event, get_calendar_list,
    update_calendar_event, delete_calendar_event, get_event_details
)
from news_briefing import fetch_and_summarize_rss

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)

