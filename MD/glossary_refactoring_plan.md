# Glossary 전처리 리팩토링 방향 보고서

**작성일**: 2026-03-05

---

## 목표

`topic_preprocessing` 스타일처럼 **파일 읽기 + 전처리 + raw_data/metadatas 반환**을
`glossary_preprocessing` 하나로 통합하여 코드 구조를 단순화한다.

---

## 현재 구조 (AS-IS)

```
RAG2.py
├── load_glossary_from_xlsx(path)   ← 파일 읽기 + raw_data/metadatas 생성
└── insert_glossary(path)           ← load → ingest 연결

glossary_utils.py
└── glossary_preprocessing(texts)   ← 텍스트 리스트 정제만 담당

rag_utils.py::SchemaIngester
└── ingest_glossary(raw_data, metadatas)
      └── raw_data = glossary_preprocessing(raw_data)  ← 정제 호출
```

**문제점**: 파일 읽기·정제·적재가 3개 파일에 흩어져 있어 흐름 파악이 어려움.

---

## 변경 구조 (TO-BE)

```
RAG2.py
└── insert_glossary(path)           ← glossary_preprocessing → ingest 연결만

glossary_utils.py
└── glossary_preprocessing(path)    ← 파일 읽기 + 정제 + raw_data/metadatas 반환

rag_utils.py::SchemaIngester
└── ingest_glossary(raw_data, metadatas)
      └── glossary_preprocessing 호출 제거 (이미 완료된 상태로 받음)
```

---

## 수정 파일 목록

| 파일 | 변경 내용 |
|---|---|
| `glossary_utils.py` | `glossary_preprocessing(texts)` → `glossary_preprocessing(path)` 로 변경. pandas `read_excel(header=1)` 로 파일 읽기 + raw_data/metadatas 생성 + 텍스트 정제 통합 |
| `RAG2.py` | `load_glossary_from_xlsx` 함수 삭제. `insert_glossary`에서 `glossary_preprocessing(path)` 직접 호출 |
| `rag_utils.py` | `ingest_glossary` 내부의 `glossary_preprocessing(raw_data)` 호출 제거 |

> [!NOTE]
> `RAG.py` (CSV 기반)도 동일하게 수정 또는 삭제 여부 결정 필요.

---

## 변경 후 호출 흐름

```
insert_glossary("파일.xlsx")
    └── raw_data, metadatas = glossary_preprocessing("파일.xlsx")
            └── pandas read_excel → 열 인덱스 접근 → 텍스트 구성 + 정제
    └── client.ingest_glossary(raw_data, metadatas)
            └── glossary_client.add_texts(texts, metadatas)  ← OpenSearch 적재
```

---

## 예상 효과

- 함수 수: 3개 → 2개 (`load_glossary_from_xlsx` 제거)
- 흐름 추적: 3개 파일 → 2개 파일
- 신규 파일 형식 추가 시: `glossary_preprocessing`만 수정하면 됨
