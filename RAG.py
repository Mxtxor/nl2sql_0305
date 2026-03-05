import os
import json
import boto3
from rag_utils import SchemaIngestConfig, SchemaIngester
from glossary_utils import glossary_preprocessing


def load_glossary_from_xlsx(path: str):
    """
    xlsx 파일을 xlwings로 파싱하여 (raw_data, metadatas) 형태로 반환한다.

    - raw_data  : OpenSearch에 임베딩될 자연어 문장 리스트 (List[str])
    - metadatas : 각 문장에 대응하는 구조화 메타 딕셔너리 리스트 (List[dict])

    xlwings를 사용하는 이유:
      사내 보안 프로그램이 pandas의 xlsx 파싱을 차단하므로,
      실제 Excel 앱을 통해 파일을 열어 데이터를 읽는 xlwings를 채택.
    """
    import xlwings as xw

    raw_data = []
    metadatas = []

    with xw.App(visible=False) as app:
        wb = app.books.open(os.path.abspath(path))
        ws = wb.sheets[0]

        # 헤더 행(1행) 읽기
        headers = ws.range('A1').expand('right').value

        # 데이터 마지막 행 확인
        last_row = ws.range('A1').expand('down').last_cell.row
        if last_row < 2:
            wb.close()
            return raw_data, metadatas

        # 데이터 행 일괄 읽기 (A2 ~ I{last_row})
        data_rows = ws.range(f'A2:I{last_row}').value
        wb.close()

    # xlwings: 단일 행은 리스트, 복수 행은 리스트의 리스트로 반환됨
    if data_rows and not isinstance(data_rows[0], list):
        data_rows = [data_rows]

    for row in data_rows:
        d = dict(zip(headers, row))

        term      = str(d.get('standard_term (논리명)')             or '').strip()
        phys      = str(d.get('standard_term_nm (물리명)')          or '').strip()
        desp      = str(d.get('standard_term_desp (표준용어 설명)') or '').strip()
        cd_nm     = str(d.get('cmn_cd_nm (공통코드명)')             or '').strip()
        cd        = str(d.get('cmn_cd (공통코드)')                  or '').strip()
        cd_grp_id = str(d.get('cd_grp_id (코드그룹아이디)')         or '').strip()
        cd_grp_nm = str(d.get('cd_grp_nm (코드그룹명)')             or '').strip()
        col_id    = str(d.get('칼럼ID')                             or '').strip()

        # 논리명이 없는 빈 행 스킵
        if not term:
            continue

        # raw_data: 임베딩 대상 자연어 텍스트 구성
        text = f"{term} ({phys}): {desp}"
        if cd_nm and cd:
            text += f" 코드값: {cd_nm}={cd}"
        raw_data.append(text)

        # metadatas: 검색 결과 활용을 위한 구조화 데이터
        metadatas.append({
            "term_name":     term,
            "physical_name": phys,
            "description":   desp,
            "cd_grp_id":     cd_grp_id,
            "cd_grp_nm":     cd_grp_nm,
            "cmn_cd_nm":     cd_nm,
            "cmn_cd":        cd,
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


def create_t2s_retriever():
    config = SchemaIngestConfig()
    client = SchemaIngester(config)
    client.ingest_topic(["hello"], metadatas=[
        {"content": "hello"},
        {"table_name": "salary"}
    ])

#def insert_topic():

#def insert_table():

if __name__ == "__main__":
    insert_glossary("glossary.xlsx")