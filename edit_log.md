# Edit Log

## 2026-03-06 16:53 — B 프로세스: tempData.xlsx 2시트 조인 적재 구현

| 파일 | 변경 종류 | 내용 |
|---|---|---|
| `glossary_utils3.py` | NEW | '렌탈멤버십채널집계' + '표준용어' 2시트 조인 전처리. 시트1 E열(칼럼ID) ↔ 시트2 D열(물리명) 대소문자 무시 매칭. 매칭 실패 시 빈 문자열로 채워 전량 적재 |
| `RAG4.py` | NEW | tempData.xlsx 적재 진입점. `rag_utils.SchemaIngester.ingest_glossary()` 재사용. `__main__`에서 `insert_glossary3("tempData.xlsx")` 호출 |

---

## 2026-03-06 16:04 — glossary2.xlsx 적재 파이프라인 신규 구현

| 파일 | 변경 종류 | 내용 |
|---|---|---|
| `glossary_utils2.py` | NEW | 7열(A~G) 단순 헤더 구조 전용 전처리 함수. `glossary_preprocessing2(path)` + `_clean2()` 헬퍼. 논리명 빈 행도 스킵 없이 적재 |
| `RAG3.py` | NEW | glossary2.xlsx 적재 진입점. `rag_utils.SchemaIngester.ingest_glossary()` 재사용. `__main__`에서 `insert_glossary2("glossary2.xlsx")` 호출 |

---

## 2026-03-06 08:56 — _clean 함수 `[NULL]` 처리 변경

| 파일 | 변경 내용 |
|---|---|
| `glossary_utils.py` | `_clean()` 함수에서 `[NULL]` 문자열을 빈 문자열(`''`) 대신 `None`으로 반환하도록 수정. 반환 타입 `str` → `str \| None` |

---

## 2026-03-05 17:27 — glossary_preprocessing 리팩토링

| 파일 | 변경 내용 |
|---|---|
| `glossary_utils.py` | `glossary_preprocessing(texts)` → `glossary_preprocessing(path)` 로 전면 교체. pandas `read_excel(header=1)` + 열 인덱스 접근 + `_clean()` 헬퍼 통합 |
| `RAG2.py` | `load_glossary_from_xlsx` 삭제. `insert_glossary`에서 `glossary_preprocessing(path)` 직접 호출로 단순화 |
| `rag_utils.py` | `ingest_glossary`의 `glossary_preprocessing(raw_data)` 중복 호출 제거. `import` 주석 처리 |

---

## 2026-03-05 15:12 — requirements.txt, Dockerfile 신규 생성

| 파일 | 변경 종류 | 내용 |
|---|---|---|
| `requirements.txt` | NEW | 프로젝트 전체 의존성 정의 (boto3, langchain, opensearch-py, openpyxl, pymysql) |
| `Dockerfile` | NEW | python:3.12-slim 기반. 기본 CMD는 `RAG2.py` |

---

## 2026-03-05 15:08 — RAG2.py 신규 생성

| 파일 | 변경 종류 | 내용 |
|---|---|---|
| `RAG2.py` | NEW | openpyxl + 열 인덱스(row[0]~row[8]) 기반 xlsx 파싱. 보안 해제 후 xlsx 직접 적재용. 1~2행 병합 헤더 스킵, 3행부터 데이터 읽기 |

---

## 2026-03-05 10:50 — Glossary 적재 파이프라인 구현 (nl2sql 프로젝트)

### 변경 파일 요약

| 파일 | 변경 종류 | 내용 |
|---|---|---|
| `glossary_utils.py` | MODIFY | `glossary_preprocessing` 함수에 텍스트 정제 로직 추가 (None 처리, 공백 정규화) |
| `RAG.py` | MODIFY | `load_glossary_from_xlsx` (xlwings 파싱) 및 `insert_glossary` 함수 추가. `__main__` 진입점을 `insert_glossary`로 변경 |
| `rag_utils.py` | MODIFY | `glossary_utils` import 주석 해제 → `glossary_preprocessing` 함수 활성화 |

## 2026-03-05 13:55 — xlsx 파싱 → CSV 파싱으로 교체 (`RAG.py`)

### 변경 파일

| 파일 | 변경 내용 |
|---|---|
| `RAG.py` | `load_glossary_from_xlsx` → `load_glossary_from_csv` 로 교체 (openpyxl → csv 내장 모듈) |
| `RAG.py` | `insert_glossary` 파라미터 `xlsx_path` → `csv_path`, 내부 호출 및 `__main__` 파일명도 csv로 변경 |

### 변경 이유
xlsx 파일이 사내 보안 프로그램에 의해 암호화되어 openpyxl로 파싱 불가(`BadZipFile`).
CSV는 순수 텍스트라 암호화 대상이 아니며, Python 내장 `csv` 모듈로 외부 라이브러리 없이 파싱 가능.

---

