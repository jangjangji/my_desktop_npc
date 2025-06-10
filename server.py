from flask import Flask, render_template, jsonify
from calendar_utils import get_today_events
from news_briefing import fetch_and_summarize_rss

app = Flask(__name__)

@app.route('/')
def index():
    events = get_today_events()
    return render_template('index.html', events=events)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)

