# 37_human_in_the_loop 작업 규칙

## 파일 역할
- `adk_human_in_the_loop.py` — **핵심만 둔다**: TransactionAgent, ApprovalToolAgent,
  `FunctionTool(execute_approved_transaction, require_confirmation=True)`(사람 승인 전까지 실제로 멈추는 지점),
  `SequentialAgent`(PaymentWorkflow), 재개 가능한 `App(resumability_config=ResumabilityConfig(is_resumable=True))`,
  `root_agent`, 사람에게 묻기 `ask_human`, 멈춤→응답→재개 루프 `handle_request`, `main`,
  안전 실행(`run_safe`, `check_api_key`, `_READY`), 상수(`APP_NAME`, `CONFIRM_CALL`).
  - Human-in-the-Loop의 세 장치(멈춤 설정, 재개 설정, 사람 응답을 돌려보내는 루프)는 모두 이 파일에 둔다.
- `payment_tools.py` — 송금 업무 (`DATA_DIR`, `_load`, `ACCOUNTS`, `POLICY`, `won`, `_balances`, `_evaluate`, `_transfer`,
  도구 `get_account`·`check_policy`·`process_payment`·`request_approval`, 승인 도구 함수 본문 `execute_approved_transaction`)
- `model_config.py` — 모델 자동 선택 (`DEFAULT_MODELS`, `resolve_model` → model, 설명, 공급자)
- `error_messages.py` — 일시적 오류 안내 문구
- `data/*.json` — 가상 계좌·정책·시나리오. 바꾸면 `tests/test_baseline.py`의 정책 판정·잔액·시나리오 수 테스트도 함께 고친다.

## 재발 방지 규칙
- 파일이 400줄을 넘으면 역할별로 나누자고 먼저 제안한다.
- 새 기능은 위 역할에 맞는 파일에 추가한다. 새 에이전트·확인(confirmation) 설정은 핵심 파일에, 송금 규칙·도구 함수는 `payment_tools.py`에 둔다.
- **승인 정책은 프롬프트가 아니라 코드로 강제한다.** 돈이 움직이는 도구는 실행 직전에 `_evaluate`로 정책을 다시 검사한다.
- **송금처럼 다시 실행되면 안 되는 도구는 멱등하게 만든다.** ADK 재개는 '최소 한 번' 실행만 보장한다.
- 실행은 `InMemoryRunner(app=app)`로 한다(재개 가능 설정). `adk web`용 `agent.py`도 `app`을 함께 내보낸다.
- 옮긴 이름은 `adk_human_in_the_loop.py`에서 `from 새모듈 import 이름  # noqa: F401`로 다시 내보내 기존 import를 유지한다.
- 실행 명령 `python adk_human_in_the_loop.py --demo [--auto]` / `"요청 문장"`과 `root_agent`, `app` 이름은 바꾸지 않는다.
- 큰 변경 전에는 커밋으로 저장 지점을 만들고, `bash .refactor/check.sh`(문법·import·테스트)가 통과해야 커밋한다.
- `handle_request`(복잡도 22)를 고칠 일이 생기면, 먼저 작은 도우미 함수로 나눈 뒤(가짜 러너 테스트가 같은지 확인) 고친다.
- 파일 구조를 바꾸면 README의 "폴더 구성"·본문의 파일 언급·"설정 바꾸기"와 `adk web` 실행 방법도 함께 고친다.
- **여러 건을 실행할 때 `asyncio.run()`을 건마다 부르지 않는다.** 이미 있는 `_LOOP_RUNNER.run(...)`(하나의 이벤트 루프)을 쓴다.
  OpenAI·Claude 연결 도구는 처음 만든 연결을 재사용하므로 루프가 바뀌면 `Event loop is closed`로 멈춘다(`tests/test_event_loop_reuse.py`로 확인).
