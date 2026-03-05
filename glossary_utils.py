import re
import pandas as pd


def glossary_preprocessing(path: str):
    """
    xlsx 파일을 읽어 raw_data(임베딩 텍스트 리스트)와
    metadatas(구조화 딕셔너리 리스트)를 반환한다.

    열 구조 (A~I열, 1~2행 병합 헤더, 데이터는 3행부터):
      A: 논리명  B: 물리명  C: 설명
      D: cd_grp_id  E: cd_grp_nm
      F: cmn_cd_nm  G: cmn_cd  H: cd_grp_eng_nm(미사용)  I: 칼럼ID

    pandas header=1 사용 이유:
      0-indexed 기준 index=1이 실제 컬럼명 행(2행).
      병합된 1행은 자동으로 스킵되고, 3행(index=2)부터 데이터로 인식됨.
    """
    df = pd.read_excel(path, header=1)

    raw_data = []
    metadatas = []

    col_names = df.columns.tolist()

    for _, row in df.iterrows():
        term = _clean(row.iloc[0])   # A: 논리명

        # 논리명이 없는 빈 행 스킵
        if not term:
            continue

        phys      = _clean(row.iloc[1])  # B: 물리명
        desp      = _clean(row.iloc[2])  # C: 설명
        cd_grp_id = _clean(row.iloc[3])  # D: 코드그룹아이디
        cd_grp_nm = _clean(row.iloc[4])  # E: 코드그룹명
        cmn_cd_nm = _clean(row.iloc[5])  # F: 공통코드명
        cmn_cd    = _clean(row.iloc[6])  # G: 공통코드
        # iloc[7]: H열 cd_grp_eng_nm (미사용)
        col_id    = _clean(row.iloc[8])  # I: 칼럼ID

        # raw_data: 임베딩 대상 자연어 텍스트 구성
        text = f"{term} ({phys}): {desp}"
        if cmn_cd_nm and cmn_cd:
            text += f" 코드값: {cmn_cd_nm}={cmn_cd}"

        # 연속 공백 정규화
        text = re.sub(r'\s+', ' ', text).strip()
        raw_data.append(text)

        # metadatas: 검색 결과 활용을 위한 구조화 데이터
        metadatas.append({
            "term_name":     term,
            "physical_name": phys,
            "description":   desp,
            "cd_grp_id":     cd_grp_id,
            "cd_grp_nm":     cd_grp_nm,
            "cmn_cd_nm":     cmn_cd_nm,
            "cmn_cd":        cmn_cd,
            "column_id":     col_id,
        })

    return raw_data, metadatas


def _clean(val) -> str:
    """NaN, None, '[NULL]' 문자열을 빈 문자열로 변환하고 앞뒤 공백 제거"""
    if val is None:
        return ''
    s = str(val).strip()
    if s.lower() in ('nan', '[null]', ''):
        return ''
    return s
