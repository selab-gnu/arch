# 34_adk_decomposition 작업 규칙

## 파일 역할
- `adk_hierarchical_report.py` — **핵심만 둔다**: 3단계 계층을 만드는 `build_report_writer`
  (L1 ReportWriter → L2 ResearchAssistant → L3 WebSearchAgent·SummarizerAgent, 모두 AgentTool로 연결),
  `SEARCH_MODE`, `root_agent`, 실행(`write_report`, `main`), 안전 실행(`run_safe`, `check_api_key`, `_READY`),
  경로·상수(`APP_NAME`, `BASE_DIR`, `REPORT_DIR`, `DEFAULT_TOPIC`).
- `search_tools.py` — L3 WebSearchAgent의 오프라인 '가상 웹' 검색 (`CORPUS_PATH`, `_load_corpus`, `search_web`)
- `trace_callbacks.py` — 실행 과정을 들여쓴 트리로 출력하는 콜백 (`LEVEL`, `_T0`, `_log`, `on_agent_start`, `on_agent_end`, `on_tool_call`)
- `model_config.py` — 모델 자동 선택 (`DEFAULT_MODELS`, `resolve_model` → model, 설명, 공급자)
- `error_messages.py` — 일시적 오류 안내 문구
- `data/web_corpus.json` — 가상 웹 문서 12건. 문서를 바꾸면 `tests/search_snapshots.json`도 다시 만든다.
- `reports/report_20261108_151533.md` — git에 들어 있는 결과 예시. 실행할 때마다 새 파일이 생기므로 새 보고서는 커밋하지 않는다.

## 재발 방지 규칙
- 파일이 400줄을 넘으면 역할별로 나누자고 먼저 제안한다.
- 새 기능은 위 역할에 맞는 파일에 추가한다. 새 계층 에이전트는 핵심 파일의 `build_report_writer`에, 그 도구는 별도 파일에 둔다.
- 새 에이전트를 추가하면 `trace_callbacks.py`의 `LEVEL`에도 이름과 단계를 넣는다(빠지면 트리 로그에 `L?`로 표시됨).
- `_T0`는 두 파일이 함께 쓰는 리스트다. `_T0[0] = ...`로 값만 바꾸고, `_T0 = ...`처럼 통째로 바꾸지 않는다.
- 옮긴 이름은 `adk_hierarchical_report.py`에서 `from 새모듈 import 이름  # noqa: F401`로 다시 내보내 기존 import를 유지한다.
- 실행 명령 `python adk_hierarchical_report.py ["주제"] [--live] [--no-save]`와 `root_agent` 이름은 바꾸지 않는다.
- 큰 변경 전에는 커밋으로 저장 지점을 만들고, `bash .refactor/check.sh`(문법·import·테스트)가 통과해야 커밋한다.
- 파일 구조를 바꾸면 README의 "폴더 구성"과 `adk web` 실행 방법도 함께 고친다.
