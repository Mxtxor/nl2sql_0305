import re

def glossary_preprocessing(texts: list) -> list:
    """
    Glossary raw_data 텍스트 리스트를 임베딩에 적합한 형태로 정제한다.

    처리 내용:
    - None 또는 빈 문자열 항목 제거
    - 앞뒤 공백 제거 (strip)
    - 연속 공백/탭/줄바꿈을 단일 공백으로 정규화
    - 마침표 누락 시 문장 끝에 마침표 추가 (선택)
    """
    cleaned = []
    for text in texts:
        if not text:
            continue
        text = str(text).strip()
        # 연속 공백, 탭, 줄바꿈 → 단일 공백
        text = re.sub(r'\s+', ' ', text)
        if not text:
            continue
        cleaned.append(text)
    return cleaned
