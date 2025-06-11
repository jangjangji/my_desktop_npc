import feedparser
from bs4 import BeautifulSoup
from summarizer import summarize_text

def extract_main_text_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    # ZDNet의 content:encoded는 <p>, <img>, <br> 등 포함
    paragraphs = soup.find_all("p")
    text = "\n".join(p.get_text(strip=True) for p in paragraphs)
    return text.strip()

def fetch_and_summarize_rss(rss_url, limit=5):
    feed = feedparser.parse(rss_url)
    print(f"총 {len(feed.entries)}개 기사 발견됨\n")
    result = []

    for entry in feed.entries[:limit]:
        title = entry.title
        link = entry.link
        print(f"📰 {title} → 요약 중...")

        html_content = ""
        if 'content' in entry and entry.content:
            html_content = entry.content[0].value
        elif 'summary' in entry:
            html_content = entry.summary

        content = extract_main_text_from_html(html_content)
        if not content:
            print(f"❗ 본문 없음, 건너뜀\n")
            continue

        try:
            summary = summarize_text(content)
        except Exception as e:
            print(f"❗ 요약 실패: {e}\n")
            continue

        result.append(f"📰 {title}\n{summary}\n🔗 {link}\n")

    return "\n".join(result)

if __name__ == "__main__":
    rss_url = "http://feeds.feedburner.com/zdkorea"
    print(fetch_and_summarize_rss(rss_url))

