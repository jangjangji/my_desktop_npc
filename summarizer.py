from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

client = OpenAI(api_key=api_key)

def summarize_text(text: str) -> str:
    prompt = "이 기사를 3~4줄로 핵심만 요약해주세요."
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt + "\n\n" + text}],
        temperature=0.5,
        max_tokens=300
    )
    return resp.choices[0].message.content.strip()

def format_meeting_notes(text: str) -> str:
    """
    회의록을 정리된 형식으로 변환합니다.
    
    Args:
        text (str): 원본 회의록 텍스트
        
    Returns:
        str: 정리된 회의록
        
    Raises:
        ValueError: 입력 텍스트가 비어있는 경우
        Exception: API 호출 실패 등 기타 오류
    """
    if not text.strip():
        raise ValueError("회의록 내용이 비어있습니다.")

    prompt = """
다음은 회의 중 작성된 원본 메모입니다. 아래 형식에 맞춰 깔끔하게 정리해 주세요.

# 형식
## 1. 회의 개요
- 주요 논의 주제
- 참석자 (파악 가능한 경우)

## 2. 주요 논의 사항
- 핵심 논의 내용을 불릿 포인트로 정리

## 3. 결정사항
- 회의에서 결정된 사항들을 명확하게 정리

## 4. 액션 아이템
- [ ] 할일 1 (담당자: OOO, 기한: OOO)
- [ ] 할일 2 (담당자: OOO, 기한: OOO)

## 5. 후속 논의 필요 사항
- 추가 논의가 필요한 사항들 정리

---
회의 메모:
""" + text

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )
    return resp.choices[0].message.content.strip()
