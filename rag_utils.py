import boto3
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path
import os
from utils import load_embedding_model
# from fewshot_utils import *
# from topic_utils import *
from glossary_utils import glossary_preprocessing
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_aws import ChatBedrock
from opensearchpy import OpenSearch
# BM25 langchain 변환
# VectorDB OpenSearch 변환
# RAG 모듈화 및 함수화 진행하여 evaluation 한번에 실행 되도록 변환
# generator 단계 노드화 진행
# duckdb RDS 교체

# 3. 임베딩 모델 초기화 (예시: OpenAI 사용 시)
# embeddings = OpenAIEmbeddings()

# 4. LangChain OpenSearch 벡터 스토어 초기화

# 5. 테스트: 데이터 추가 (최초 실행 시 인덱스가 자동 생성됨)
# texts = ["이 문서는 테스트용 데이터입니다.", "오픈서치 엔드포인트 연결 성공!"]
# vector_db.add_texts(texts)

# 6. 테스트: 유사도 검색
# docs = vector_db.similarity_search("테스트 문서 찾아줘", k=1)
# print(docs[0].page_content)

@dataclass
class SchemaIngestConfig:
    """스키마 인제스트 설정"""

    # Opensearch 설정
    opensearch_url = "https://vpc-skix-dp-p-os-tx2sql-py4gfstedn6m74bysc7qhitiau.ap-northeast-2.es.amazonaws.com:443"
    http_auth = ("admin", "Password12!")
    db_name: str = "text2sql_db"
    topic_collection_name: str = "topic_collection"
    glossary_collection_name: str = "glossary_collection"
    fewshot_collection_name: str = "fewshot_collection"

    # Embedding 설정
    embedding_model: str = "amazon.titan-embed-text-v2:0"
    embedding_dim: int = 1024
    titan_region: str = "ap-northeast-2"

    # BM25 인덱스 경로
    bm25_index_path: str = "rag2_test/data/bm25_text2sql_index.pkl"

    # def __post_init__(self):
    #     """경로를 절대 경로로 변환"""
    #     project_root = Path(__file__).resolve().parents[2]

    #     if not os.path.isabs(self.schema_info_path):
    #         self.schema_info_path = str(project_root / self.schema_info_path)
    #     if not os.path.isabs(self.table_relationships_path):
    #         self.table_relationships_path = str(project_root / self.table_relationships_path)
    #     if not os.path.isabs(self.query_patterns_path):
    #         self.query_patterns_path = str(project_root / self.query_patterns_path)

class TitanEmbeddingProvider:
    """Amazon Titan Embeddings via Bedrock"""

    def __init__(self, config: SchemaIngestConfig):
        self.config = config
        self.client_embedding = load_embedding_model()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """여러 개의 문서를 한 번에 벡터로 변환합니다."""
        # 입력받은 texts(리스트)를 실제 임베딩 모델에 통과시켜 벡터(숫자 배열)로 만듭니다.
        return self.client_embedding.embed_documents(texts)

    def embed_query(self, texts):

        return self.client_embedding.embed_query(texts)

class SchemaIngester:
    """
    스키마 인제스트 메인 클래스

    1. Schema Collection: Table + Column + Relationship 청크
    2. Few-shot Collection: Query Pattern 예제
    """

    def __init__(self, config: SchemaIngestConfig):
        self.config = config
        # self.embeddings_provider = TitanEmbeddingProvider(config)
        self.embedding = TitanEmbeddingProvider(config)
        opensearch_client = OpenSearch(hosts=[config.opensearch_url], http_auth=config.http_auth)
        self.glossary_client = OpenSearchVectorSearch(
                                    index_name=config.glossary_collection_name,
                                    embedding_function=self.embedding,
                                    opensearch_url=config.opensearch_url,
                                    http_auth=config.http_auth,
                                    engine='lucene')

        self.topic_client = OpenSearchVectorSearch(
                                    index_name=config.topic_collection_name,
                                    embedding_function=self.embedding,
                                    opensearch_url=config.opensearch_url,
                                    http_auth=config.http_auth,
                                    engine='lucene')

        self.fewshot_client = OpenSearchVectorSearch(
                                    index_name=config.fewshot_collection_name,
                                    embedding_function=self.embedding,
                                    opensearch_url=config.opensearch_url,
                                    http_auth=config.http_auth,
                                    engine='lucene')

        response = opensearch_client.info()
        print("✅ 통신 성공! OpenSearch 서버가 정상적으로 응답합니다.")
        print(f"📌 클러스터 이름: {response.get('cluster_name')}")
        print(f"📌 OpenSearch 버전: {response.get('version', {}).get('number')}")

    def relevant_glossary(self, query, top_k=3):

        response = self.glossary_client.similarity_search(query= query,
            k=top_k,
            search_kwargs={
                "_source": ["term_name", "synonyms", "code_value"]
            })

        return response

    def relevant_fewshot(self, query, top_k=3):

        search_query = {
            "size": top_k,
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": text,
                                "fields": ["content", "sql_query"],
                                "fuzziness": "AUTO"
                            }
                        } for text in query # 리스트 표현식으로 여러 match 쿼리 생성
                    ]
                }
            }
        }

        response = self.fewshot_client.similarity_search(query= query,
                                                        k=top_k,
                                                        search_kwargs={
                                                            "_source": ["term_name", "synonyms", "code_value"]
                                                        })

        return response

    def relevant_topic(self, query, top_k=3):


        response = self.topic_client.similarity_search(query= query,
                                                        k=top_k,
                                                        search_kwargs={
                                                            "_source": ["term_name", "synonyms", "code_value"]
                                                        })


        return response

    def ingest_topic(self, raw_data, metadatas) -> Dict[str,int]:


        # raw_data = topic_preprocessing(raw_data)
        doc_ids = self.topic_client.add_texts(texts=raw_data,
                                              metadatas=metadatas)

        print(f" ->Topic  {len(doc_ids)}개의 데이터 Insert 완료")

    def ingest_fewshot(self, raw_data, metadatas) -> Dict[str,int]:
        raw_data = fewshot_preprocessing(raw_data)

        doc_ids = self.fewshot_client.add_texts(texts=raw_data,
                                                metadatas=metadatas)

        print(f" ->Fewshot  {len(doc_ids)}개의 데이터 Insert 완료")

    def ingest_glossary(self, raw_data, metadatas) -> Dict[str,int]:

        raw_data = glossary_preprocessing(raw_data)
        doc_ids = self.glossary_client.add_texts(texts=raw_data,
                                                 metadatas=metadatas)

        print(f" ->Glossary  {len(doc_ids)}개의 데이터 Insert 완료")