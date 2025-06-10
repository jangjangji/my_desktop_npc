from flask import Flask, render_template, request, jsonify
from news_briefing import fetch_and_summarize_rss

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/summarize", methods=["GET"])
def summarize():
    rss_url = request.args.get("rss", default="https://feeds.feedburner.com/zdkorea")
    result = fetch_and_summarize_rss(rss_url, limit=5)
    return jsonify({"summary": result})

if __name__ == "__main__":
    app.run(port=5005)

