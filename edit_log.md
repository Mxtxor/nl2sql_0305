# Edit Log

## 2026-03-05 10:50 — Glossary 적재 파이프라인 구현 (nl2sql 프로젝트)

### 변경 파일 요약

| 파일 | 변경 종류 | 내용 |
|---|---|---|
| `glossary_utils.py` | MODIFY | `glossary_preprocessing` 함수에 텍스트 정제 로직 추가 (None 처리, 공백 정규화) |
| `RAG.py` | MODIFY | `load_glossary_from_xlsx` (xlwings 파싱) 및 `insert_glossary` 함수 추가. `__main__` 진입점을 `insert_glossary`로 변경 |
| `rag_utils.py` | MODIFY | `glossary_utils` import 주석 해제 → `glossary_preprocessing` 함수 활성화 |

### 비고
- xlsx 파싱 라이브러리로 `xlwings` 채택 (사내 보안 정책으로 pandas 사용 불가)
- `glossary.xlsx` 기준 9개 컬럼, 1개 데이터 행 파싱 로컬 검증 완료
