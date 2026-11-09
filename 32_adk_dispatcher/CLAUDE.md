# 32_adk_dispatcher 작업 규칙

## 파일 역할
- `adk_coordinator_dispatcher.py` — **핵심만 둔다**: 전문가 에이전트(BillingSpecialist, TechSupportSpecialist), 코디네이터(CoordinatorAgent),
  `root_agent`, 실행 도우미(`ask`, `run_demo`, `run_chat`), 안전 실행(`run_safe`, `check_api_key`, `_READY`), 진입점.
- `support_tools.py` — 상담 도구(청구 4개, 진단 3개)와 data/*.json 읽기 (`DATA_DIR`, `_load`, `BILLING_DB`, `DIAGNOSTICS_KB`)
- `model_config.py` — 모델 자동 선택 (`DEFAULT_MODELS`, `resolve_model` → model, 설명, 공급자)
- `error_messages.py` — 일시적 오류 안내 문구

## 재발 방지 규칙
- 파일이 400줄을 넘으면 역할별로 나누자고 먼저 제안한다.
- 새 기능은 위 역할에 맞는 파일에 추가한다. 새 전문가 에이전트는 핵심 파일에, 그 도구는 `support_tools.py`에 둔다.
- 옮긴 이름은 `adk_coordinator_dispatcher.py`에서 `from 새모듈 import 이름  # noqa: F401`로 다시 내보내 기존 import를 유지한다.
- 실행 명령 `python adk_coordinator_dispatcher.py [--demo]`와 `root_agent` 이름은 바꾸지 않는다.
- 큰 변경 전에는 커밋으로 저장 지점을 만들고, `bash .refactor/check.sh`(문법·import·테스트)가 통과해야 커밋한다.
- 도구의 동작을 일부러 바꿨다면 `tests/tool_snapshots.json`을 다시 만들고 그 이유를 커밋 메시지에 적는다.
- 파일 구조를 바꾸면 README의 "폴더 구성"과 `adk web` 실행 방법도 함께 고친다.
