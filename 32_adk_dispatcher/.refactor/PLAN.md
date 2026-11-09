# 분리 계획 — adk_coordinator_dispatcher.py (426줄)

## 원칙 (31번과 동일)
- **핵심은 원래 파일에 남긴다**: 전문가 에이전트 2개(BillingSpecialist, TechSupportSpecialist), 코디네이터(CoordinatorAgent),
  `root_agent`, 실행 도우미 `ask`·`run_demo`·`run_chat`, 진입점(`__main__`), 안전 실행 `run_safe`·`check_api_key`·`_READY`,
  모델 결정 호출 `MODEL, MODEL_LABEL, MODEL_PROVIDER = resolve_model()`, 경고·로그 숨김 설정.
- 실행 명령(`python adk_coordinator_dispatcher.py [--demo]`)과 `root_agent` 이름은 바꾸지 않는다.
- 옮긴 이름은 원래 파일에서 `from 새모듈 import ...  # noqa: F401`로 다시 내보낸다.
- 잘라 옮기기만 하고 로직은 바꾸지 않는다. 안 쓰게 된 import는 지운다.

## 의존 관계 / 전역 변수
- `MODEL*`: 가져올 때 한 번 정해짐 → 원래 파일. `_READY`: `run_safe`만 바꿈 → 원래 파일에 그대로.
- 도구 7개 → `BILLING_DB`, `DIAGNOSTICS_KB` → `_load`, `DATA_DIR` (도구와 함께 옮김). `run_demo`도 `_load` 사용 → import.
- `BILLING_DB`·`DIAGNOSTICS_KB`는 읽기만 함(환불 기록은 session.state에) → 모듈 이동 안전.
- 문자열 참조(getattr/globals/eval/pickle) 없음. 다른 폴더에서 이 파일을 import하는 곳 없음.

## 단계
1. **model_config.py** ← `DEFAULT_MODELS`, `_has_key`, `_provider_of`, `resolve_model` (31번과 달리 공급자까지 3개 반환)
2. **support_tools.py** ← `DATA_DIR`, `_load`, `BILLING_DB`, `DIAGNOSTICS_KB` + 청구 도구 4개 + 진단 도구 3개
3. **error_messages.py** ← `TRANSIENT_ERROR_PATTERN`, `_error_text`, `transient_error_message`
4. README.md 의 폴더 구성·설정 위치·`adk web` 실행 방법 갱신 (현재 안내는 파일 1개를 복사하는 방식이라 분리 후 동작 안 함)

예상 결과: 원래 파일 약 190줄, 새 파일 3개.
