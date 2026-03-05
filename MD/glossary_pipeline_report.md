# Glossary 적재 파이프라인 구축 보고서

**작성일**: 2026-03-05   
**대상 프로젝트**: `nl2sql` — Text2SQL RAG 시스템

---

## 1. 개요

NL2SQL 시스템에서 자연어 질의를 SQL로 변환할 때, 도메인 용어사전(Glossary)을 벡터 검색으로 제공하기 위한 **Glossary 적재 파이프라인**을 구축하였다.

### 적재 흐름

```
glossary.xlsx
    │
    ▼
load_glossary_from_xlsx()   ← RAG.py
    │  xlwings로 xlsx 파싱
    │  → raw_data (List[str])
    │  → metadatas (List[dict])
    │
    ▼
ingest_glossary(raw_data, metadatas)   ← SchemaIngester (rag_utils.py)
    │
    ├─ glossary_preprocessing(raw_data)  ← glossary_utils.py (텍스트 정제)
    │
    └─ glossary_client.add_texts(texts=raw_data, metadatas=metadatas)
            │
            ▼
       OpenSearch Vector DB (glossary_collection)
```

---

## 2. 주요 로직 및 설계 이유

### 2.1 xlsx 파싱 — `load_glossary_from_xlsx` (`RAG.py`)

#### 핵심 코드
```python
import xlwings as xw

with xw.App(visible=False) as app:
    wb = app.books.open(os.path.abspath(path))
    ws = wb.sheets[0]
    headers = ws.range('A1').expand('right').value
    last_row = ws.range('A1').expand('down').last_cell.row
    data_rows = ws.range(f'A2:I{last_row}').value
    wb.close()
```

#### 설계 이유
| 결정 사항 | 이유 |
|---|---|
| **xlwings 사용** | 사내 보안 프로그램이 pandas의 xlsx 파싱 처리를 차단. xlwings는 실제 Excel 앱을 통해 파일을 열기 때문에 보안 정책 우회 가능 |
| **`visible=False`** | Excel 앱이 화면에 표시되지 않도록 처리. 서버/배치 환경에서 UI 없이 실행 가능 |
| **단일 행 예외 처리** | xlwings는 데이터가 단일 행이면 `List`, 복수 행이면 `List[List]`를 반환하는 특성이 있어, `isinstance` 체크로 두 케이스를 통합 처리 |
| **빈 행 스킵** | `논리명(standard_term)`이 없는 행은 의미 없는 빈 행으로 판단, `continue`로 건너뜀 |

---

### 2.2 `raw_data` vs `metadatas` 분리 전략

OpenSearch의 `add_texts(texts, metadatas)` 구조에서 각 인자의 역할:

| 인자 | 역할 | 담는 내용 |
|---|---|---|
| `texts` (raw_data) | **벡터 임베딩 대상** — 자연어 유사도 검색의 기준 | `"{논리명} ({물리명}): {설명} 코드값: {코드명}={코드}"` 형태의 자연어 문장 |
| `metadatas` | **검색 결과와 함께 반환되는 구조화 데이터** — SQL 생성 시 참조 | `term_name`, `physical_name`, `cmn_cd`, `cmn_cd_nm`, `column_id` 등 딕셔너리 |

#### raw_data 텍스트 구성 예시
```
교환유형코드 (EXCH_TYPE_CD): 교환 유형을 정의하는 코드다. 코드값: 동종교환=01
```

#### 설계 이유
- **`raw_data`를 자연어 문장으로 구성**: LLM이 *"교환 종류에 따라 필터링"* 같이 자연어로 질의할 때, 논리명·물리명·설명·코드값 정보가 하나의 문장에 담겨 있어야 의미 유사도 검색이 정확하게 동작함
- **`metadatas`에 구조화 값 보존**: 검색 후 실제 SQL 생성 단계에서 `WHERE EXCH_TYPE_CD = '01'` 처럼 코드값을 꺼내 쓸 수 있도록, 정제 전 원본 필드값을 별도 보존

---

### 2.3 텍스트 정제 — `glossary_preprocessing` (`glossary_utils.py`)

#### 핵심 코드
```python
import re

def glossary_preprocessing(texts: list) -> list:
    cleaned = []
    for text in texts:
        if not text:
            continue
        text = str(text).strip()
        text = re.sub(r'\s+', ' ', text)  # 연속 공백/탭/줄바꿈 → 단일 공백
        if not text:
            continue
        cleaned.append(text)
    return cleaned
```

#### 설계 이유
| 처리 항목 | 이유 |
|---|---|
| **None·빈 문자열 제거** | OpenSearch 임베딩 API에 빈 텍스트가 들어가면 오류 또는 노이즈 발생 방지 |
| **연속 공백 정규화** | xlsx 셀에서 읽어온 텍스트에 탭, 줄바꿈이 섞여 있을 수 있음. 임베딩 품질을 위해 단일 공백으로 정규화 |
| **strip()** | 앞뒤 공백은 벡터 유사도에 불필요한 노이즈 |

---

### 2.4 적재 흐름 연결 — `ingest_glossary` + `insert_glossary`

```python
# RAG.py
def insert_glossary(xlsx_path: str):
    config = SchemaIngestConfig()
    client = SchemaIngester(config)
    raw_data, metadatas = load_glossary_from_xlsx(xlsx_path)
    client.ingest_glossary(raw_data, metadatas)

# rag_utils.py — SchemaIngester
def ingest_glossary(self, raw_data, metadatas):
    raw_data = glossary_preprocessing(raw_data)  # 정제
    doc_ids = self.glossary_client.add_texts(texts=raw_data, metadatas=metadatas)
    print(f" ->Glossary {len(doc_ids)}개의 데이터 Insert 완료")
```

#### 설계 이유
- **`load_glossary_from_xlsx`와 `ingest_glossary` 분리**: 파싱 로직과 적재 로직을 분리하여 향후 다른 소스(DB, API 등)에서 데이터를 가져와도 `ingest_glossary`를 그대로 재사용 가능
- **`glossary_preprocessing`을 `ingest_glossary` 내부에서 호출**: 전처리가 적재 전에 반드시 실행되도록 강제화. 호출부에서 전처리를 빠뜨리는 실수 방지

---

## 3. 변경 파일 목록

| 파일 | 변경 내용 |
|---|---|
| `glossary_utils.py` | `glossary_preprocessing` 텍스트 정제 로직 구현 |
| `RAG.py` | `load_glossary_from_xlsx`, `insert_glossary` 함수 추가 |
| `rag_utils.py` | `glossary_preprocessing` import 활성화 |
| `edit_log.md` | 변경 이력 기록 |

---

## 4. 검증 결과

### 로컬 파싱 검증 (OpenSearch 연결 없이)

`glossary.xlsx` 기준 파싱 및 정제 로직 단위 테스트 수행:

```
[파싱 결과] 총 1개 항목

--- 항목 1 ---
[raw_data]  교환유형코드 (EXCH_TYPE_CD): 교환 유형을 정의하는 코드다. 코드값: 동종교환=01
[metadata]  {'term_name': '교환유형코드', 'physical_name': 'EXCH_TYPE_CD',
             'description': '교환 유형을 정의하는 코드다.', 'cd_grp_id': '',
             'cd_grp_nm': '', 'cmn_cd_nm': '동종교환', 'cmn_cd': '01',
             'column_id': 'exch_type_id'}
```

✅ `raw_data` 자연어 문장 정상 생성  
✅ `metadatas` 구조화 데이터 정상 구성  
✅ 빈 행(None 포함 행) 자동 스킵 정상 동작  

### 다음 검증 단계 (OpenSearch 연결 후)

```python
# 실제 적재 후 검색 검증 예시
insert_glossary("glossary.xlsx")
results = client.relevant_glossary("교환 유형 코드")
for doc in results:
    print(doc.page_content)
    print(doc.metadata["cmn_cd"])  # → "01"
```

---

## 5. 향후 고려 사항

| 항목 | 내용 |
|---|---|
| **동일 논리명 다중 코드값 처리** | 같은 용어에 코드값이 여러 개(01, 02, ...)인 경우, 현재는 행 수만큼 별도 벡터 생성. 필요 시 그룹화하여 코드 목록을 하나의 텍스트로 합칠 수 있음 |
| **증분 적재** | 현재는 전체 재적재 방식. 향후 중복 체크 및 업데이트 로직 추가 필요 |
| **xlwings 서버 환경 제약** | xlwings는 Excel 앱이 설치된 Windows 환경에서만 동작. Linux 서버 배포 시에는 openpyxl이나 다른 라이브러리로 교체 필요 |
