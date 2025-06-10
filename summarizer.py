from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def summarize_text(text):
    prompt = "이 기사를 3~4줄로 핵심만 요약해주세요."
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt + "\n\n" + text}],
        temperature=0.5,
        max_tokens=300
    )
    return resp.choices[0].message.content.strip()

