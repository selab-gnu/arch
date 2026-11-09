# 분리 계획 — adk_generator_critic.py (454줄)

## 원칙 (31~34번과 동일)
- **핵심은 원래 파일에 남긴다**: Generator, Critic, 루프 종료 검사 에이전트 `ExitConditionChecker`,
  `LoopAgent`(ValidationLoop), `root_agent`, 실행(`load_questions`, `solve`, `show`, `main`),
  안전 실행(`run_safe`, `check_api_key`, `_READY`), 경로·상수(`APP_NAME`, `BASE_DIR`, `QUESTIONS_PATH`, `MAX_ITERATIONS`),
  모델 결정 호출, 경고·로그 숨김 설정.
  - `ExitConditionChecker`는 이 예제가 보여 주려는 "루프를 끝내는 방법" 그 자체라서 핵심 파일에 남긴다.
- 실행 명령(`python adk_generator_critic.py [번호|all|"질문"]`)과 `root_agent` 이름은 바꾸지 않는다.
- 옮긴 이름은 원래 파일에서 `from 새모듈 import ...  # noqa: F401`로 다시 내보낸다.
- 잘라 옮기기만 하고 로직은 바꾸지 않는다. 안 쓰게 된 import는 지운다.

## 의존 관계 / 전역 변수
- `MODEL*`: 가져올 때 한 번 정해짐 → 원래 파일. `_READY`: `run_safe`만 바꿈 → 원래 파일.
- `SCHEMA_SQL`: 가져올 때 `SCHEMA_PATH`에서 한 번 읽음, 이후 읽기만 함 → `SCHEMA_PATH`와 함께 옮김.
- `new_db` ← `validate_sql`, `run_sql` / `run_sql` ← `same_result`, `show` / `clean_sql` ← `validate_sql`, `solve`.
  → DB·SQL 함수를 한 파일에 모으고, 원래 파일은 `clean_sql`, `run_sql`, `same_result`, `schema_for_prompt`를 가져다 씀.
- `show`가 `sqlite3.Error`를 잡으므로 원래 파일의 `import sqlite3`는 남김.
- 문자열 참조(getattr/globals/eval/pickle) 없음. 다른 폴더에서 이 파일을 import하는 곳 없음.

## 단계
1. **model_config.py** ← `DEFAULT_MODELS`, `_has_key`, `_provider_of`, `resolve_model` (32~34번과 같은 내용)
2. **error_messages.py** ← `TRANSIENT_ERROR_PATTERN`, `_error_text`, `transient_error_message` (32~34번과 같은 내용)
3. **sql_tools.py** ← `SCHEMA_PATH`, `SCHEMA_SQL`, `new_db`, `schema_for_prompt`, `clean_sql`, `validate_sql`(Critic 도구),
   `run_sql`, `same_result`(채점) — 쇼핑몰 DB와 SQL 실행·검증·채점
4. README.md 의 폴더 구성·설정 위치·`adk web` 실행 방법 갱신

예상 결과: 원래 파일 약 250줄, 새 파일 3개.
복잡한 함수: `solve`(19)·`main`(16)은 핵심 파일에 남고, `resolve_model`(14)은 옮기기만 함 — 이번에는 쪼개지 않음.
