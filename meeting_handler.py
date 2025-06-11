# meeting_handler.py

from summarizer import format_meeting_notes
from typing import Dict, Union

def process_meeting_notes(raw_text: str) -> Dict[str, str]:
    """
    회의 메모 원문을 받아서 정리된 회의록을 반환합니다.
    
    Returns:
        Dict[str, str]: {
            'status': 'success' 또는 'error',
            'message': 성공 시 정리된 회의록, 실패 시 에러 메시지,
            'processing_status': 처리 상태 메시지
        }
    """
    try:
        result = {
            'status': 'processing',
            'message': '',
            'processing_status': '회의록 정리 중...'
        }
        
        if not raw_text.strip():
            return {
                'status': 'error',
                'message': '❗ 회의록 내용이 비어있습니다.',
                'processing_status': '처리 실패'
            }

        cleaned_summary = format_meeting_notes(raw_text)
        
        return {
            'status': 'success',
            'message': cleaned_summary,
            'processing_status': '처리 완료'
        }
        
    except Exception as e:
        error_message = str(e)
        if "api_key" in error_message.lower():
            error_detail = "API 키 설정을 확인해주세요."
        elif "timeout" in error_message.lower():
            error_detail = "서버 응답 시간이 초과되었습니다."
        else:
            error_detail = "알 수 없는 오류가 발생했습니다."
            
        return {
            'status': 'error',
            'message': f"❗ 회의록 정리 실패: {error_detail}\n상세 에러: {str(e)}",
            'processing_status': '처리 실패'
        }

