import os
from rag_utils import SchemaIngestConfig, SchemaIngester
from glossary_utils import glossary_preprocessing


def load_glossary_from_xlsx(path: str):
    """
    xlsx 파일을 openpyxl로 파싱하여 (raw_data, metadatas) 형태로 반환한다.

    - raw_data  : OpenSearch에 임베딩될 자연어 문장 리스트 (List[str])
    - metadatas : 각 문장에 대응하는 구조화 메타 딕셔너리 리스트 (List[dict])

    열 구조 (A~I열, 1~2행 병합 헤더, 데이터는 3행부터):
      A(0): 논리명  B(1): 물리명  C(2): 설명
      D(3): cd_grp_id  E(4): cd_grp_nm
      F(5): cmn_cd_nm  G(6): cmn_cd  H(7): cd_grp_eng_nm  I(8): 칼럼ID
    """
    import openpyxl

    raw_data = []
    metadatas = []

    wb = openpyxl.load_workbook(os.path.abspath(path))
    ws = wb.active

    # 1~2행은 병합 헤더 → 스킵, 3행(min_row=3)부터 데이터
    for row in ws.iter_rows(min_row=3, values_only=True):
        # A열(논리명)이 비어있는 빈 행 스킵
        if not row[0] or not str(row[0]).strip():
            continue

        term      = str(row[0] or '').strip()  # A: 논리명
        phys      = str(row[1] or '').strip()  # B: 물리명
        desp      = str(row[2] or '').strip()  # C: 설명
        cd_grp_id = str(row[3] or '').strip()  # D: 코드그룹아이디
        cd_grp_nm = str(row[4] or '').strip()  # E: 코드그룹명
        cmn_cd_nm = str(row[5] or '').strip()  # F: 공통코드명
        cmn_cd    = str(row[6] or '').strip()  # G: 공통코드
        # row[7] : H열 cd_grp_eng_nm (현재 미사용)
        col_id    = str(row[8] or '').strip()  # I: 칼럼ID

        # raw_data: 임베딩 대상 자연어 텍스트 구성
        text = f"{term} ({phys}): {desp}"
        if cmn_cd_nm and cmn_cd:
            text += f" 코드값: {cmn_cd_nm}={cmn_cd}"
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


def insert_glossary(xlsx_path: str):
    """
    xlsx 파일을 파싱하여 Glossary 데이터를 OpenSearch에 적재한다.
    """
    config = SchemaIngestConfig()
    client = SchemaIngester(config)

    raw_data, metadatas = load_glossary_from_xlsx(xlsx_path)
    print(f"[Glossary] 파싱 완료: {len(raw_data)}개 항목")

    client.ingest_glossary(raw_data, metadatas)


if __name__ == "__main__":
    insert_glossary("목 록 코 드 정 리 (to-be)_v0.2.xlsx")
