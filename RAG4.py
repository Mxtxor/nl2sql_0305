from rag_utils import SchemaIngestConfig, SchemaIngester
from glossary_utils3 import glossary_preprocessing3


def insert_glossary3(xlsx_path: str):
    """
    tempData.xlsx의 두 시트를 조인하여 Glossary 데이터를
    OpenSearch glossary_collection에 적재한다.

    - 시트1 '렌탈멤버십채널집계': 테이블ID/테이블명/칼럼ID/칼럼명 제공
    - 시트2 '표준용어': 논리명/물리명/설명 제공
    - 조인 기준: 시트1 E열(칼럼ID) ↔ 시트2 D열(물리명), 대소문자 무시
    """
    config = SchemaIngestConfig()
    client = SchemaIngester(config)

    raw_data, metadatas = glossary_preprocessing3(xlsx_path)
    print(f"[Glossary3] 파싱 완료: {len(raw_data)}개 항목")

    client.ingest_glossary(raw_data, metadatas)


if __name__ == "__main__":
    insert_glossary3("tempData.xlsx")
