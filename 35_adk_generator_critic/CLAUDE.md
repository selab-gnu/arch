# 35_adk_generator_critic 작업 규칙

## 파일 역할
- `adk_generator_critic.py` — **핵심만 둔다**: Generator, Critic, 루프 종료 검사 에이전트 `ExitConditionChecker`,
  `LoopAgent`(ValidationLoop), `root_agent`, 실행(`load_questions`, `solve`, `show`, `main`),
  안전 실행(`run_safe`, `check_api_key`, `_READY`), 경로·상수(`APP_NAME`, `BASE_DIR`, `QUESTIONS_PATH`, `MAX_ITERATIONS`).
  - `ExitConditionChecker`는 이 예제가 보여 주는 "루프를 끝내는 방법" 자체이므로 핵심 파일에 둔다.
- `sql_tools.py` — 쇼핑몰 DB와 SQL 도구 (`SCHEMA_PATH`, `SCHEMA_SQL`, `new_db`, `schema_for_prompt`, `clean_sql`,
  Critic 도구 `validate_sql`, 채점 `run_sql`·`same_result`)
- `model_config.py` — 모델 자동 선택 (`DEFAULT_MODELS`, `resolve_model` → model, 설명, 공급자)
- `error_messages.py` — 일시적 오류 안내 문구
- `data/shop_schema.sql`, `data/questions.json` — 실습 DB와 문제·정답 SQL.
  바꾸면 `tests/sql_snapshots.json`을 다시 만들고, 문제 수·번호를 확인하는 테스트도 함께 고친다.

## 재발 방지 규칙
- 파일이 400줄을 넘으면 역할별로 나누자고 먼저 제안한다.
- 새 기능은 위 역할에 맞는 파일에 추가한다. 새 에이전트는 핵심 파일에, DB·SQL 관련 함수나 Critic 도구는 `sql_tools.py`에 둔다.
- DB는 항상 `new_db()`로 메모리에 새로 만들어 쓴다. 원본 `data/shop_schema.sql`을 직접 바꾸는 코드를 넣지 않는다.
- 옮긴 이름은 `adk_generator_critic.py`에서 `from 새모듈 import 이름  # noqa: F401`로 다시 내보내 기존 import를 유지한다.
- 실행 명령 `python adk_generator_critic.py [번호|all|"질문"]`과 `root_agent` 이름은 바꾸지 않는다.
- 큰 변경 전에는 커밋으로 저장 지점을 만들고, `bash .refactor/check.sh`(문법·import·테스트)가 통과해야 커밋한다.
- `solve`(복잡도 19)·`main`(16)을 고칠 일이 생기면, 먼저 작은 도우미 함수로 나눈 뒤(테스트가 같은지 확인) 고친다.
- 파일 구조를 바꾸면 README의 "폴더 구성"·"설정 바꾸기"와 `adk web` 실행 방법도 함께 고친다.
- **여러 건을 실행할 때 `asyncio.run()`을 건마다 부르지 않는다.** 이미 있는 `_LOOP_RUNNER.run(...)`(하나의 이벤트 루프)을 쓴다.
  OpenAI·Claude 연결 도구는 처음 만든 연결을 재사용하므로 루프가 바뀌면 `Event loop is closed`로 멈춘다(`tests/test_event_loop_reuse.py`로 확인).
