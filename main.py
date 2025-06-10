# main.py
from calendar_utils import get_today_events

if __name__ == "__main__":
    print(" 오늘의 일정:")
    events = get_today_events()
    if isinstance(events, str):
        print(events)
    else:
        for e in events:
            print(f"- {e['time']}: {e['title']}")

