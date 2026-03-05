import os
from rag_utils import SchemaIngestConfig, SchemaIngester
from glossary_utils import glossary_preprocessing


def insert_glossary(xlsx_path: str):
    """
    xlsx 파일을 파싱하여 Glossary 데이터를 OpenSearch에 적재한다.
    파일 읽기·정제·raw_data/metadatas 생성은 glossary_preprocessing에서 담당.
    """
    config = SchemaIngestConfig()
    client = SchemaIngester(config)

    raw_data, metadatas = glossary_preprocessing(xlsx_path)
    print(f"[Glossary] 파싱 완료: {len(raw_data)}개 항목")

    client.ingest_glossary(raw_data, metadatas)


if __name__ == "__main__":
    insert_glossary("목 록 코 드 정 리 (to-be)_v0.2.xlsx")
