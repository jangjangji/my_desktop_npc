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
당신은 회의록 정리 전문가입니다. 주어진 회의록을 마크다운 형식으로 깔끔하게 정리해주세요.

중요한 규칙:
1. 원본 내용에 없는 내용을 임의로 추가하지 마세요.
2. 원본의 맥락과 의미를 그대로 유지하세요.
3. 명확하게 언급된 내용만 포함하세요.
4. 참석자는 실제 언급된 사람만 기재하세요.
5. 불확실한 내용은 생략하세요.

형식:
# 회의 메모

## 1. 회의 개요
- 주요 논의 주제: (원본에서 명시된 경우만 작성)
- 참석자: (원본에서 명시된 경우만 작성)

## 2. 주요 논의 사항
(원본 내용을 bullet point로 정리)

## 3. 결정사항
(명확하게 결정된 사항만 기재)

## 4. 액션 아이템
(명확하게 할당된 업무만 기재)
- [ ] 담당자와 기한이 명시된 경우만 작성

## 5. 후속 논의 필요 사항
(추가 논의가 필요하다고 명시된 사항만 기재)

---
원본 회의록:
""" + text

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 회의록 정리 전문가입니다. 원본 내용을 충실히 반영하여 깔끔하게 정리하는 것이 목표입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    return resp.choices[0].message.content.strip()
