# cli.py
from summarizer import summarize_text

def main():
    print("📎 복붙한 문서를 입력하고 'end'를 입력하면 요약합니다.\n")

    buffer = []
    while True:
        line = input()
        if line.strip().lower() == "end":
            break
        buffer.append(line)

    input_text = "\n".join(buffer)
    print("\n🤖 요약 중...\n")
    summary = summarize_text(input_text)
    print("✅ 요약 결과:\n")
    print(summary)

if __name__ == "__main__":
    main()

