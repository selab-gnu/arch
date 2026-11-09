# 분리 계획 — adk_sequential_pipeline.py (434줄)

## 원칙
- **핵심은 원래 파일에 남긴다**: 세 에이전트(Parser/Extractor/Summarizer), `SequentialAgent` 조립, `root_agent`,
  `run_pipeline`(조립 라인 실행), 진입점 `main`·`check_api_key`, 모델 결정 호출 `MODEL, MODEL_LABEL = resolve_model()`,
  경고·로그 숨김 설정(가져올 때 바로 실행되는 코드).
- 실행 명령(`python adk_sequential_pipeline.py ...`)과 `root_agent` 이름은 바꾸지 않는다.
- 옮긴 이름은 원래 파일에서 `from 새모듈 import ...  # noqa: F401`로 다시 내보낸다 (기존 import 유지).
- 코드는 잘라 옮기기만 하고 로직은 바꾸지 않는다. 옮긴 뒤 안 쓰게 된 import는 지운다.

## 의존 관계 / 전역 변수
- `MODEL`, `MODEL_LABEL`: 가져올 때 한 번 정해지고 바뀌지 않음 → 원래 파일에 둔다 (state.py 불필요).
- `pdf_parser` → `MAX_CHARS` (같이 옮김) / `collect_pdfs` → `DATA_DIR`, `make_sample_pdf` (같이 옮김).
- `check_api_key` → `MODEL_LABEL`, `_has_key` → 원래 파일에 두고 `_has_key`만 import.
- 문자열 참조(getattr/globals/eval/pickle) 없음. 다른 폴더에서 이 파일을 import하는 곳 없음.

## 단계
1. **model_config.py** ← `DEFAULT_MODELS`, `_has_key`, `_provider_of`, `resolve_model` (모델 자동 선택)
2. **pdf_tools.py** ← `MAX_CHARS`, `pdf_parser`, `_PATTERNS`, `regex_extractor`, `summary_engine` (에이전트가 쓰는 도구)
3. **pdf_inputs.py** ← `make_sample_pdf`, `DATA_DIR`, `collect_pdfs` (처리할 PDF 고르기·샘플 만들기)
4. **error_messages.py** ← `TRANSIENT_ERROR_PATTERN`, `_error_text`, `transient_error_message` (오류 안내 문구)
5. (선택) `resolve_model`(복잡도 14) 를 "공급자·모델 이름 고르기"와 "모델 객체 만들기" 두 도우미로 쪼개기 — 동작 동일
6. README.md 의 파일 구조 설명에 새 파일 추가

예상 결과: 원래 파일 약 190줄, 새 파일 4개(각 30~100줄).
