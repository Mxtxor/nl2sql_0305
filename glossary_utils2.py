import re
import pandas as pd


def glossary_preprocessing2(path: str):
    """
    glossary2.xlsx 파일을 읽어 raw_data(임베딩 텍스트 리스트)와
    metadatas(구조화 딕셔너리 리스트)를 반환한다.

    열 구조 (A~G열, 1행 헤더, 데이터는 2행부터 / 병합 없음):
      A: 논리명(term)  B: 물리명(phys)  C: 설명(desp)
      D: 테이블ID(table_id)  E: 테이블명(table_nm)
      F: 칼럼ID(col_id)  G: 칼럼명(col_nm)

    참고:
      - header=0 : 1행이 컬럼명 행, 2행부터 데이터
      - usecols="A:G" : A~G 열만 읽기
      - nrows=19 : 최대 19행(A2~G20) 데이터 읽기
      - 논리명(term)이 비어 있어도 스킵 없이 적재한다.
    """
    df = pd.read_excel(path, header=0, usecols="A:G", nrows=19)

    raw_data = []
    metadatas = []

    for _, row in df.iterrows():
        term     = _clean2(row.iloc[0])   # A: 논리명
        phys     = _clean2(row.iloc[1])   # B: 물리명
        desp     = _clean2(row.iloc[2])   # C: 설명
        table_id = _clean2(row.iloc[3])   # D: 테이블ID
        table_nm = _clean2(row.iloc[4])   # E: 테이블명
        col_id   = _clean2(row.iloc[5])   # F: 칼럼ID
        col_nm   = _clean2(row.iloc[6])   # G: 칼럼명

        # raw_data: 임베딩 대상 자연어 텍스트 구성
        text = f"{term} ({phys}): {desp}"
        if table_nm or table_id:
            text += f" 테이블: {table_nm}({table_id})"
        if col_nm or col_id:
            text += f" 칼럼: {col_nm}({col_id})"

        # 연속 공백 정규화
        text = re.sub(r'\s+', ' ', text).strip()
        raw_data.append(text)

        # metadatas: 검색 결과 활용을 위한 구조화 데이터
        metadatas.append({
            "term_name":     term,
            "physical_name": phys,
            "description":   desp,
            "table_id":      table_id,
            "table_nm":      table_nm,
            "col_id":        col_id,
            "col_nm":        col_nm,
        })

    return raw_data, metadatas


def _clean2(val) -> str | None:
    """NaN, None을 빈 문자열로, '[NULL]' 문자열은 None으로 변환하고 앞뒤 공백 제거"""
    if val is None:
        return ''
    s = str(val).strip()
    if s.lower() == '[null]':
        return None
    if s.lower() in ('nan', ''):
        return ''
    return s
