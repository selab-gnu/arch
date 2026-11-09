# 분리 계획 — adk_human_in_the_loop.py (492줄)

## 원칙 (31~36번과 동일)
- **핵심은 원래 파일에 남긴다**: TransactionAgent, ApprovalToolAgent(+ `FunctionTool(execute_approved_transaction,
  require_confirmation=True)`로 '실제로 멈추는' 지점), `SequentialAgent`(PaymentWorkflow),
  재개 가능한 `App(resumability_config=...)`, `root_agent`, 사람에게 묻기 `ask_human`, 멈춤→응답→재개 루프 `handle_request`,
  `main`, 안전 실행(`run_safe`, `check_api_key`, `_READY`), 상수(`APP_NAME`, `CONFIRM_CALL`), 모델 결정 호출, 경고·로그 숨김 설정.
  - Human-in-the-Loop의 핵심(멈춤 설정, 재개 설정, 사람 응답을 돌려보내는 루프)이 모두 원래 파일에 보이도록 한다.
- 실행 명령(`python adk_human_in_the_loop.py --demo [--auto]` / `"요청 문장"`)과 `root_agent`, `app` 이름은 바꾸지 않는다.
- 옮긴 이름은 원래 파일에서 `from 새모듈 import ...  # noqa: F401`로 다시 내보낸다.
- 잘라 옮기기만 하고 로직은 바꾸지 않는다. 안 쓰게 된 import는 지운다.

## 의존 관계 / 전역 변수
- `MODEL*`: 가져올 때 한 번 정해짐 → 원래 파일. `_READY`: `run_safe`만 바꿈 → 원래 파일.
- `ACCOUNTS`, `POLICY`: 가져올 때 한 번 읽고 이후 읽기만 함(잔액은 session.state에 복사해서 바꿈) → 도구와 함께 옮김.
- 송금 도구 5개 → `_evaluate`, `_transfer`, `_balances`, `won`, `ACCOUNTS`, `POLICY` (모두 함께 옮김).
- 원래 파일에 남는 `ask_human`(ACCOUNTS, won), `handle_request`(won), `main`(_load)은 새 파일에서 가져다 씀.
- `execute_approved_transaction` 함수 본문은 도구 파일로 옮기되, `require_confirmation=True`로 감싸는 부분은 원래 파일에 남김.
- 문자열 참조(getattr/globals/eval/pickle) 없음. 다른 폴더에서 이 파일을 import하는 곳 없음.

## 준비 중 발견한 사소한 점 (고치지 않고 테스트에 그대로 고정)
- 거래처 등록 여부는 이름의 앞뒤 공백을 지우고 비교하지만, 사유 문구에는 입력한 이름이 공백까지 그대로 들어감.
- 인자 없이 실행하면 사용법 끝 표시로 '다른 모델'을 찾는데 독스트링에 그 말이 없어 '모델 지정 예' 줄까지 출력됨.
- 멱등 키는 계좌 ID를 대문자로 바꾸기 전 글자로 만들어서, `OPS-001`과 `ops-001`은 다른 송금으로 취급됨.

## 단계
1. **model_config.py** ← `DEFAULT_MODELS`, `_has_key`, `_provider_of`, `resolve_model` (32~36번과 같은 내용)
2. **error_messages.py** ← `TRANSIENT_ERROR_PATTERN`, `_error_text`, `transient_error_message` (32~36번과 같은 내용)
3. **payment_tools.py** ← `DATA_DIR`, `_load`, `ACCOUNTS`, `POLICY`, `won`, 송금 공통 로직(`_balances`, `_evaluate`, `_transfer`),
   TransactionAgent 도구(`get_account`, `check_policy`, `process_payment`, `request_approval`),
   ApprovalToolAgent 도구 함수(`execute_approved_transaction`)
4. README.md 의 폴더 구성·설정 위치·`adk web` 실행 방법 갱신

예상 결과: 원래 파일 약 230줄, 새 파일 3개.
복잡한 함수: `handle_request`(22)는 핵심 파일에 남고, `resolve_model`(14)은 옮기기만 함 — 이번에는 쪼개지 않음.
