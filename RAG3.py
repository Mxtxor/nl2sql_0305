from rag_utils import SchemaIngestConfig, SchemaIngester
from glossary_utils2 import glossary_preprocessing2


def insert_glossary2(xlsx_path: str):
    """
    glossary2.xlsx 파일을 파싱하여 Glossary 데이터를 OpenSearch glossary_collection에 적재한다.
    파일 읽기·정제·raw_data/metadatas 생성은 glossary_preprocessing2에서 담당.

    대상 파일 열 구조 (A~G열, 1행 헤더, 병합 없음):
      A: 논리명  B: 물리명  C: 설명
      D: 테이블ID  E: 테이블명  F: 칼럼ID  G: 칼럼명
    """
    config = SchemaIngestConfig()
    client = SchemaIngester(config)

    raw_data, metadatas = glossary_preprocessing2(xlsx_path)
    print(f"[Glossary2] 파싱 완료: {len(raw_data)}개 항목")

    client.ingest_glossary(raw_data, metadatas)


if __name__ == "__main__":
    insert_glossary2("glossary2.xlsx")
