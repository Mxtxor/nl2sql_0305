import re
import pandas as pd


def glossary_preprocessing3(path: str):
    """
    tempData.xlsx의 두 시트를 조인하여 raw_data(임베딩 텍스트 리스트)와
    metadatas(구조화 딕셔너리 리스트)를 반환한다.

    [시트1] '렌탈멤버십채널집계'
      - 헤더: 3행 (header=2, 0-indexed)
      - 데이터: 4행~23행 (nrows=20)
      - 사용 열: C(테이블ID), D(테이블명), E(칼럼ID, 조인키), F(칼럼명)

    [시트2] '표준용어'
      - 헤더: 1행 (header=0)
      - 사용 열: C(논리명), D(물리명, 조인키), M(설명)

    [조인 로직]
      시트1의 E열(칼럼ID) 기준으로 시트2 D열(물리명)을 대소문자 무시 매칭.
      매칭 성공 → 논리명, 물리명, 설명 채움.
      매칭 실패 → 논리명, 물리명, 설명을 '' (빈 문자열)로 채워 그대로 적재.

    [적재 포맷]
      RAG3.py (A 프로세스)와 동일한 metadatas 키 구조 사용.
    """
    # ── 시트1 읽기: 렌탈멤버십채널집계 ──────────────────────────────
    # header=2 → 3번 행(0-indexed=2)이 헤더
    # usecols="C:F" → C~F 열만 읽기
    # nrows=20 → 4행~23행 (데이터 20행)
    df_channel = pd.read_excel(
        path,
        sheet_name="렌탈멤버십채널집계",
        header=2,
        usecols="C:F",
        nrows=20,
    )

    # ── 시트2 읽기: 표준용어 ────────────────────────────────────────
    # header=0 → 1번 행이 헤더
    # usecols=[2, 3, 12] → C(index 2), D(index 3), M(index 12) 열만 읽기
    df_term = pd.read_excel(
        path,
        sheet_name="표준용어",
        header=0,
        usecols=[2, 3, 12],
    )

    # 시트2 컬럼명을 내부 식별자로 고정 (엑셀 헤더 텍스트와 무관)
    df_term.columns = ["term_name", "physical_name", "description"]

    # 조인맵 생성: { 물리명.lower() → (논리명, 물리명, 설명) }
    # 물리명이 비어있는 행은 맵에서 제외
    join_map = {}
    for _, trow in df_term.iterrows():
        phys_key = _clean3(trow["physical_name"])
        if phys_key:
            join_map[phys_key.lower()] = (
                _clean3(trow["term_name"]),
                phys_key,
                _clean3(trow["description"]),
            )

    # ── 시트1 순회 + 조인 ────────────────────────────────────────────
    raw_data = []
    metadatas = []

    for _, row in df_channel.iterrows():
        table_id = _clean3(row.iloc[0])   # C: 테이블ID
        table_nm = _clean3(row.iloc[1])   # D: 테이블명
        col_id   = _clean3(row.iloc[2])   # E: 칼럼ID (조인키)
        col_nm   = _clean3(row.iloc[3])   # F: 칼럼명

        # 칼럼ID가 없으면 의미 없는 행 → 스킵
        if not col_id:
            continue

        # 대소문자 무시 조인
        matched = join_map.get(col_id.lower())
        if matched:
            term_name, phys_name, description = matched
        else:
            # 매칭 실패: 논리명/물리명/설명을 빈 문자열로 채워 적재
            term_name   = ''
            phys_name   = ''
            description = ''

        # raw_data: 임베딩 대상 자연어 텍스트 구성 (A 프로세스와 동일)
        text = f"{term_name} ({phys_name}): {description}"
        if table_nm or table_id:
            text += f" 테이블: {table_nm}({table_id})"
        if col_nm or col_id:
            text += f" 칼럼: {col_nm}({col_id})"

        # 연속 공백 정규화
        text = re.sub(r'\s+', ' ', text).strip()
        raw_data.append(text)

        # metadatas: A 프로세스(RAG3.py)와 동일한 키 구조
        metadatas.append({
            "term_name":     term_name,
            "physical_name": phys_name,
            "description":   description,
            "table_id":      table_id,
            "table_nm":      table_nm,
            "column_id":        col_id,
            "column_nm":        col_nm,
        })

    return raw_data, metadatas


def _clean3(val) -> str:
    """NaN, None → '', '[NULL]' → None, 앞뒤 공백 제거"""
    if val is None:
        return ''
    s = str(val).strip()
    if s.lower() == '[null]':
        return None
    if s.lower() in ('nan', ''):
        return ''
    return s
