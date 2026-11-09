# 31_adk_sequential_pipeline 작업 규칙

## 파일 역할
- `adk_sequential_pipeline.py` — **핵심만 둔다**: 세 에이전트(Parser/Extractor/Summarizer), `SequentialAgent` 조립, `root_agent`, `run_pipeline`, `check_api_key`, `main`.
- `pdf_tools.py` — 에이전트가 쓰는 도구 함수 (`pdf_parser`, `regex_extractor`, `summary_engine`, `MAX_CHARS`, `_PATTERNS`)
- `model_config.py` — 모델 자동 선택 (`DEFAULT_MODELS`, `resolve_model`)
- `pdf_inputs.py` — 명령행 인자 → PDF 목록, 샘플 PDF 생성
- `error_messages.py` — 일시적 오류 안내 문구

## 재발 방지 규칙
- 파일이 400줄을 넘으면 역할별로 나누자고 먼저 제안한다.
- 새 기능은 위 역할에 맞는 파일에 추가한다. 핵심 파일에는 에이전트 조립·실행 코드만 둔다.
- 옮긴 이름은 `adk_sequential_pipeline.py`에서 `from 새모듈 import 이름  # noqa: F401`로 다시 내보내 기존 import를 유지한다.
- 실행 명령 `python adk_sequential_pipeline.py ...`와 `root_agent` 이름은 바꾸지 않는다.
- 큰 변경 전에는 커밋으로 저장 지점을 만들고, `bash .refactor/check.sh`(문법·import·테스트)가 통과해야 커밋한다.
- 파일 구조를 바꾸면 README의 "폴더 구성"과 `adk web` 실행 방법도 함께 고친다.
- **여러 건을 실행할 때 `asyncio.run()`을 건마다 부르지 않는다.** 이미 있는 `_LOOP_RUNNER.run(...)`(하나의 이벤트 루프)을 쓴다.
  OpenAI·Claude 연결 도구는 처음 만든 연결을 재사용하므로 루프가 바뀌면 `Event loop is closed`로 멈춘다(`tests/test_event_loop_reuse.py`로 확인).
