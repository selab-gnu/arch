# 분리 계획 — adk_hierarchical_report.py (396줄)

## 원칙 (31~33번과 동일)
- **핵심은 원래 파일에 남긴다**: 3단계 계층을 만드는 `build_report_writer`(L1 ReportWriter → L2 ResearchAssistant
  → L3 WebSearchAgent·SummarizerAgent, AgentTool 연결), `SEARCH_MODE`, `root_agent`, 실행(`write_report`, `main`),
  안전 실행(`run_safe`, `check_api_key`, `_READY`), 경로·상수(`APP_NAME`, `BASE_DIR`, `REPORT_DIR`, `DEFAULT_TOPIC`),
  모델 결정 호출, 경고·로그 숨김 설정.
- 실행 명령(`python adk_hierarchical_report.py ["주제"] [--live] [--no-save]`)과 `root_agent` 이름은 바꾸지 않는다.
- 옮긴 이름은 원래 파일에서 `from 새모듈 import ...  # noqa: F401`로 다시 내보낸다.
- 잘라 옮기기만 하고 로직은 바꾸지 않는다. 안 쓰게 된 import는 지운다.

## 의존 관계 / 전역 변수
- `MODEL*`: 가져올 때 한 번 정해짐 → 원래 파일. `_READY`: `run_safe`만 바꿈 → 원래 파일.
- `_T0`(실행 시작 시각): `write_report`가 `_T0[0] = ...`로 **리스트 안의 값만** 바꾸고, `_log`가 읽음.
  리스트 객체 자체는 그대로이므로 `trace_callbacks.py`로 옮겨 `from trace_callbacks import _T0`로 가져와도 같은 리스트를 공유함
  (변수를 통째로 바꾸는 `_T0 = ...` 형태가 아니라서 안전). 테스트로 확인.
- `search_web` → `_load_corpus` → `CORPUS_PATH` (함께 옮김. 새 파일에서도 같은 폴더 기준 경로로 계산).
- 문자열 참조(getattr/globals/eval/pickle) 없음. 다른 폴더에서 이 파일을 import하는 곳 없음.

## 단계
1. **model_config.py** ← `DEFAULT_MODELS`, `_has_key`, `_provider_of`, `resolve_model` (32·33번과 같은 내용)
2. **error_messages.py** ← `TRANSIENT_ERROR_PATTERN`, `_error_text`, `transient_error_message` (32·33번과 같은 내용)
3. **search_tools.py** ← `CORPUS_PATH`, `_load_corpus`, `search_web` (L3 WebSearchAgent의 오프라인 '가상 웹' 검색)
4. **trace_callbacks.py** ← `LEVEL`, `_T0`, `_log`, `on_agent_start`, `on_agent_end`, `on_tool_call` (계층 실행 과정을 들여쓴 트리로 출력)
5. README.md 의 폴더 구성·설정 위치·`adk web` 실행 방법 갱신

예상 결과: 원래 파일 약 220줄, 새 파일 4개.
복잡한 함수: `resolve_model`(14, 옮기기만), `main`(11, 핵심 파일에 남음) — 이번에는 쪼개지 않음.
