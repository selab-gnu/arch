# ADK Human-in-the-Loop 예제 — 법인 송금 승인

Google ADK(Agent Development Kit)로 구현한 **Human-in-the-Loop(안전망) 패턴** 실습 예제입니다.
일상적인 송금은 에이전트가 바로 처리하고, 고위험 송금(한도 초과·신규 거래처)은 **실행을 실제로 멈추고 사람의 승인**을 받은 뒤에만 실행합니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다. 멈춤과 재개는 ADK의 도구 확인(Tool Confirmation) 기능으로 구현했습니다.

**Gemini · Claude · OpenAI 모두 지원합니다.** Claude Code에서 쓰는 Anthropic API 키나 Codex에서 쓰는 OpenAI API 키가 터미널에 설정되어 있으면, 코드를 고치지 않고 그대로 실행됩니다(키를 자동으로 감지). → [API 키 설정](#api-키-설정)

## 구조

```
workflow = SequentialAgent([TransactionAgent, ApprovalToolAgent])     ← App(resumable=True)로 실행

① TransactionAgent (일상 처리)
     check_policy ─┬─ auto              → process_payment ─────────────▶ 즉시 송금
                   ├─ blocked (잔액 부족) → 송금하지 않고 안내
                   └─ requires_approval → request_approval (= ApprovalTool)
                                           └─▶ state["pending_approval"] 에 등록 (아직 송금 안 함)
② ApprovalToolAgent
     대기 건이 있으면 execute_approved_transaction 호출
        └─ require_confirmation=True
             → ADK가 실행을 멈추고 adk_request_confirmation 이벤트 발생   ⏸️
             → 사람이 승인/거절을 응답(FunctionResponse)
             → 멈춘 자리에서 재개                                         ▶️
                  승인: 송금 실행 / 거절: "This tool call is rejected." → 취소 안내
```

| 구성 요소 | 역할 |
|---|---|
| `TransactionAgent` | 송금 요청 분석 → 정책 판정 → 일상 건은 처리, 고위험 건은 승인 대기열 등록 |
| `request_approval` | 블로그의 **ApprovalTool**. 고위험 거래를 `pending_approval`에 올리기만 하고 송금하지 않음 |
| `ApprovalToolAgent` | 대기 건을 실행하는 도구를 호출 → 이 도구에 걸린 확인 요청으로 **실제로 멈춤** |
| `execute_approved_transaction` | `FunctionTool(..., require_confirmation=True)`. 사람이 승인해야 함수 본문이 실행됨 |
| 사람 (터미널) | 거래 내용과 승인 사유를 보고 승인/거절 + 승인자 이름·의견 입력 |

### 송금 정책 (`data/policy.json`)

| 조건 | 결과 |
|---|---|
| 잔액 부족, 없는 계좌, 0원 이하 | **차단** (승인 요청도 하지 않음) |
| 100만 원 초과 | **사람 승인 필요** |
| 등록되지 않은(신규) 거래처 | **사람 승인 필요** (소액이어도) |
| 그 외 | 자동 처리 |

## 의사코드를 그대로 쓰면 안 되는 이유 — 세 가지 함정

블로그 의사코드는 `ApprovalToolAgent`에게 "Pause execution and request human input"이라고 **지시**만 합니다. 실제로 동작하게 만들면서 확인한 함정과 해결책은 다음과 같습니다.

### 1. 지시만으로는 멈추지 않는다 → 도구 확인(`require_confirmation`)

LLM에게 "멈추고 물어봐"라고 써도 LLM은 텍스트로 질문을 출력할 뿐, 실행은 그대로 끝납니다.
ADK의 `FunctionTool(func, require_confirmation=True)`를 쓰면, 그 도구가 호출될 때 ADK가 함수를 실행하지 않습니다. 대신 `adk_request_confirmation` 이벤트를 내고 **실행을 멈춥니다**. 클라이언트(이 예제에서는 터미널)가 승인/거절을 `FunctionResponse`로 돌려보내면 거기서 이어집니다.

> `require_confirmation`에는 `True` 대신 함수를 넘겨 **인자를 보고 승인 필요 여부를 결정**할 수도 있습니다(예: 금액이 크면 True).

### 2. 재개하면 처음부터 다시 돈다 → `ResumabilityConfig(is_resumable=True)`

ADK 2.11에서 같은 구성으로 실험한 결과:

| 실행 방식 | 승인 응답 후 일어난 일 | 결과 |
|---|---|---|
| 기본 (`InMemoryRunner(agent=workflow)`) | `SequentialAgent`가 **처음부터 다시** 실행 → TransactionAgent의 일상 처리가 **한 번 더** 실행됨 | 실제 결제라면 **중복 송금** |
| `App(..., resumability_config=ResumabilityConfig(is_resumable=True))` | **멈춘 자리(ApprovalToolAgent)부터** 재개 | 정상, 모델 호출도 줄어듦 |

그래서 이 예제는 `InMemoryRunner(app=App(...resumable...))`로 실행합니다.

### 3. 재개는 "최소 한 번"만 보장한다 → 멱등(idempotent) 송금

ADK 문서는 재개 시 도구가 **최소 한 번(at-least-once)** 실행된다고만 보장합니다(다시 실행될 수 있음).
그래서 송금 함수 `_transfer`는 (계좌, 거래처, 금액, 메모)로 **멱등 키**를 만들어, 같은 송금이 다시 들어오면 새로 송금하지 않고 기존 결과(`already_processed`)를 돌려줍니다.

### 덧붙여: 정책은 프롬프트가 아니라 코드로 강제

`process_payment`는 호출될 때마다 정책을 **다시 검사**하고, 자동 처리 대상이 아니면 거부(`refused`)합니다.
LLM이 instruction을 어기고 고액을 바로 송금하려 해도 코드가 막습니다. 테스트에서 "실수하는 LLM"을 흉내 내 일부러 고액을 `process_payment`로 보냈습니다. 코드가 거부했고, 이후 승인 절차로 넘어가는 것을 확인했습니다.

## 폴더 구성

```
37_human_in_the_loop/
├── adk_human_in_the_loop.py   # 이 예제
├── README.md
└── data/
    ├── accounts.json          # 가상 회사 '경상테크'의 법인 계좌 3개, 등록 거래처 4곳
    ├── policy.json            # 자동 처리 한도(100만 원), 신규 거래처 승인 규칙
    └── requests.json          # --demo 시나리오 5개 (+ --auto용 승인/거절 결정)
```

모든 데이터는 가상입니다. 잔액 변경과 거래 원장은 **실행 중 메모리(세션 상태)에서만** 바뀌고 파일은 바뀌지 않습니다. 요청마다 새 세션이라 잔액은 매번 처음 값에서 시작합니다.

### 데모 시나리오 (`data/requests.json`)

| # | 요청 | 정책 판정 | 사람의 결정 (`--auto`) | 결과 |
|---|---|---|---|---|
| 1 | 운영 계좌 → 클라우드나인 호스팅 85만 원 | 자동 처리 | — | 즉시 송금 |
| 2 | 운영 계좌 → 한빛 소프트웨어 라이선스 1,200만 원 | 한도 초과 | 승인 | ⏸️ → 송금 |
| 3 | 운영 계좌 → 퀵마켓 컨설팅 1,850만 원 | 한도 초과 + 신규 거래처 | 거절 | ⏸️ → 취소 |
| 4 | 연구개발 계좌 → 데이터랩스 30만 원 | 신규 거래처 (소액이어도) | 승인 | ⏸️ → 송금 |
| 5 | 연구개발 계좌 → 진주 시설관리 500만 원 | 잔액 부족 | — | 차단 |

## 설치

Python 3.10 이상이 필요합니다.

```bash
cd 37_human_in_the_loop
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -U google-adk

# 사용할 모델에 따라 하나 더 설치 (Gemini만 쓰면 생략)
pip install -U anthropic       # Claude (Anthropic API 키)
pip install -U openai          # OpenAI GPT (OpenAI API 키)
```

## API 키 설정

아래 키 중 **하나만** 설정되어 있으면 프로그램이 알아서 감지해 해당 모델을 씁니다. 실행하면 어떤 모델을 쓰는지 먼저 표시됩니다.

```
🧠 사용 모델: Claude (claude-sonnet-5-5, Anthropic API 키)
```

| 쓰는 도구 / 키 | 설정 | 기본 모델 | 추가 설치 |
|---|---|---|---|
| **Gemini** (Google AI Studio) | `export GOOGLE_API_KEY="..."` | `gemini-3.8-flash` | — |
| **Claude Code**에서 쓰는 **Anthropic API 키** | `export ANTHROPIC_API_KEY="sk-ant-..."` | `claude-sonnet-5-5` | `pip install anthropic` |
| **Codex**에서 쓰는 **OpenAI API 키** | `export OPENAI_API_KEY="sk-..."` | `gpt-5.6` | `pip install openai` |
| Vertex AI (Google Cloud) | `export GOOGLE_GENAI_USE_VERTEXAI=TRUE`<br>`export GOOGLE_CLOUD_PROJECT="..."`<br>`export GOOGLE_CLOUD_LOCATION="us-central1"` | `gemini-3.8-flash` | `gcloud auth application-default login` |

> 실행을 멈추고 승인받는 기능(`require_confirmation`)과 재개는 모델이 아니라 ADK가 처리하므로 **Gemini·Claude·OpenAI 어느 모델로도 똑같이 동작**합니다.

### Claude Code · Codex를 쓰고 있다면

이미 Claude Code나 Codex를 **API 키로** 쓰고 있다면, 그 키가 들어 있는 터미널에서 바로 실행하면 됩니다.

```bash
echo $ANTHROPIC_API_KEY     # Claude Code용 키가 보이면 → Claude로 실행됨
echo $OPENAI_API_KEY        # Codex용 키가 보이면     → OpenAI로 실행됨
python adk_human_in_the_loop.py --demo
```

> **구독 계정으로 로그인해서 쓰는 경우는 해당되지 않습니다.**
> Claude Code에 Claude 구독(Pro/Max 등)으로 로그인했거나, Codex에 ChatGPT 계정으로 로그인했다면, 이 로그인 정보는 API 키가 아니어서 이 프로그램에서 쓸 수 없습니다.
> 이때는 [Anthropic Console](https://console.anthropic.com) 또는 [OpenAI Platform](https://platform.openai.com/api-keys)에서 **API 키를 따로 발급**받아 위처럼 설정하세요. API 사용량은 구독과 별도로 과금됩니다.

### 키가 여러 개일 때 / 모델을 직접 고를 때

자동 감지 순서는 **Gemini → Claude → OpenAI**입니다. 다른 것을 쓰려면 지정하세요.

```bash
# 공급자만 고르기 (기본 모델 사용)
ADK_PROVIDER=claude python adk_human_in_the_loop.py --demo
ADK_PROVIDER=openai python adk_human_in_the_loop.py --demo

# 모델 이름까지 직접 지정 (이름으로 공급자를 판단: claude-* → Claude, gpt-*/o* → OpenAI, 그 외 → Gemini)
ADK_MODEL=claude-opus-5-5 python adk_human_in_the_loop.py --demo
ADK_MODEL=gpt-5.6-luna    python adk_human_in_the_loop.py --demo
```

> **Claude를 Anthropic API 키로 쓸 때 주의**: ADK에 `model="claude-sonnet-5-5"`처럼 이름만 넘기면, ADK는 이것을 **Vertex AI(Google Cloud)의 Claude**로 연결해 Google Cloud 프로젝트를 요구합니다.
> 이 예제는 Anthropic API 키가 있으면 `AnthropicLlm(model=...)` 객체로 감싸서 Anthropic API로 직접 연결합니다(코드의 `resolve_model()` 참고).

> `python`으로 직접 실행할 때는 위처럼 터미널에서 export해야 합니다. `adk web`은 에이전트 폴더의 `.env` 파일에 키를 적으면 읽습니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 실행

```bash
# 1) 데모 시나리오 5개 — 승인/거절은 터미널에서 직접 입력 (수업 시연용)
python adk_human_in_the_loop.py --demo

# 2) 데모 시나리오 5개 — requests.json의 결정으로 자동 응답 (빠른 확인용)
python adk_human_in_the_loop.py --demo --auto

# 3) 직접 요청하기
python adk_human_in_the_loop.py "운영 계좌(OPS-001)에서 그린오피스 사무용품에 사무가구 2,300,000원을 송금해 줘."
```

### 출력 예시 (시나리오 2 — 고액 송금 승인)

```
======================================================================
▶ 시나리오 2: 고액 송금 (사람 승인 → 승인)
  요청: 운영 계좌(OPS-001)에서 한빛 소프트웨어 라이선스에 연간 라이선스 비용 12,000,000원을 송금해 줘.
======================================================================
  🔧 [TransactionAgent] check_policy({"from_account": "OPS-001", "payee": "한빛 소프트웨어 라이선스", "amount_krw": 12000000})
     ↳ {'decision': 'requires_approval', 'reasons': ['자동 처리 한도(1,000,000원) 초과']}
  🔧 [TransactionAgent] request_approval({... "amount_krw": 12000000, "memo": "연간 라이선스 비용"})
     ↳ {'status': 'queued', 'reasons': ['자동 처리 한도(1,000,000원) 초과']}

  🤖 TransactionAgent: 한도를 넘는 송금이라 승인 대기열에 올렸습니다. 승인자 결재를 기다립니다.
  🔧 [ApprovalToolAgent] execute_approved_transaction({"request_id": "APR-001"})

  ──────────────────────────────────────────────────────────────
  ⏸️  실행이 멈췄습니다 — 사람의 승인이 필요합니다 (Human-in-the-Loop)
     요청 ID : APR-001
     출금    : OPS-001 (운영 계좌)
     받는 곳 : 한빛 소프트웨어 라이선스
     금액    : 12,000,000원
     목적    : 연간 라이선스 비용
     승인 사유: 자동 처리 한도(1,000,000원) 초과
  ──────────────────────────────────────────────────────────────
  승인하시겠습니까? [y/N]: y
  승인자 이름: 이선아 팀장
  의견(선택): 연간 계약서 확인함
  ▶️  승인 응답을 보내고, 멈춘 자리에서 재개합니다.
     ↳ {'status': 'success', 'tx_id': 'TX-1108-141530-3F2A'}

  🤖 ApprovalToolAgent: 송금이 완료되었습니다. 거래번호 TX-1108-141530-3F2A, 12,000,000원, 승인자 이선아 팀장, 잔액 36,000,000원.

  📒 이번 요청으로 처리된 송금: 1건
     TX-1108-141530-3F2A  OPS-001 → 한빛 소프트웨어 라이선스  12,000,000원  (승인: 이선아 팀장, 잔액 36,000,000원)
```

> 에이전트의 안내 문장과 메모는 LLM이 작성하므로 실행할 때마다 다를 수 있습니다. 정책 판정과 송금 처리는 코드가 하므로 항상 같습니다.
> 거절(`n` 또는 Enter)하면 `This tool call is rejected.`가 반환되고 송금은 실행되지 않습니다.

### 웹 UI로 실행 (`adk web`)

```bash
mkdir -p hitl_agent
cp adk_human_in_the_loop.py hitl_agent/agent.py
cp -r data hitl_agent/data
echo "from . import agent" > hitl_agent/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > hitl_agent/.env      # 또는 ANTHROPIC_API_KEY=... / OPENAI_API_KEY=...
adk web                              # 브라우저에서 http://localhost:8000 → hitl_agent 선택
```

웹 UI에서도 도구 확인 요청 이벤트가 표시되지만, 응답 방식은 ADK 버전에 따라 다를 수 있습니다. 또 `adk web`이 이 파일의 `app`(재개 가능 설정) 대신 `root_agent`를 불러오면 위 함정 2의 재시작 동작이 나타날 수 있습니다. 멈춤과 재개를 정확히 관찰하려면 **명령행 실행을 권장**합니다.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 모델 공급자 | `export ADK_PROVIDER=gemini` / `claude` / `openai` | 설정된 키로 자동 감지 |
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` (또는 `claude-opus-5-5`, `gpt-5.6-luna` …) | 공급자별 기본 모델 |
| 공급자별 기본 모델 | 코드의 `DEFAULT_MODELS` | Gemini `gemini-3.8-flash` · Claude `claude-sonnet-5-5` · OpenAI `gpt-5.6` |
| 자동 처리 한도 | `data/policy.json`의 `auto_approve_limit_krw` | 1,000,000원 |
| 신규 거래처 승인 | `data/policy.json`의 `require_approval_for_new_payee` | `true` |
| 계좌·거래처 | `data/accounts.json` | 계좌 3개, 거래처 4곳 |
| 데모 시나리오 | `data/requests.json` | 5개 |

## 문제 해결

| 증상 | 원인과 해결 |
|---|---|
| `ModuleNotFoundError: google.adk` | 가상환경을 활성화했는지 확인하고 `pip install -U google-adk` |
| `API 키가 설정되어 있지 않습니다` | `echo $GOOGLE_API_KEY $ANTHROPIC_API_KEY $OPENAI_API_KEY`로 현재 터미널에 키가 있는지 확인. 다른 터미널 창이나 IDE에서 설정한 키는 보이지 않을 수 있음 |
| `❌ API 키 인증 실패` (`Unauthorized`, `401`) | 키 값 오타, 만료된 키, 또는 **구독 로그인 정보를 키로 착각**한 경우. 콘솔에서 API 키를 새로 발급 |
| `Claude를 쓰려면 anthropic 패키지가 필요합니다` / `OpenAI 모델을 쓰려면 openai 패키지가 필요합니다` | `pip install -U anthropic` / `pip install -U openai` |
| `GOOGLE_CLOUD_PROJECT ... must be set` (Claude 사용 시) | Claude가 Vertex AI로 연결된 경우. `ANTHROPIC_API_KEY`를 설정하고 `GOOGLE_GENAI_USE_VERTEXAI`는 해제 |
| 의도와 다른 공급자가 선택됨 | 키가 여러 개 설정됨. `ADK_PROVIDER=claude`처럼 직접 지정 |
| `404 ... model not found` / `model_not_found` | 계정에서 쓸 수 없는 모델 이름. 각 공급자의 모델 목록에서 확인해 `ADK_MODEL`로 지정 |
| 고액인데 승인 없이 끝남 | 정책상 '차단'(잔액 부족 등)일 수 있음. `check_policy` 결과(↳ 줄) 확인 |
| 승인 후 TransactionAgent가 또 실행됨 | `App(..., resumability_config=ResumabilityConfig(is_resumable=True))` 없이 실행한 경우 (`adk web` 포함) |
| `ApprovalToolAgent`가 대기 건을 못 찾음 | TransactionAgent가 `request_approval`을 호출하지 않음. 더 강한 모델을 쓰거나 instruction 강조 |

## 실습 과제 아이디어

1. **함정 직접 확인하기**: `main()`의 `InMemoryRunner(app=app)`를 `InMemoryRunner(agent=workflow, app_name=APP_NAME)`로 바꿔 시나리오 2를 실행해 보세요. 승인 후 TransactionAgent가 다시 도는 것을 확인할 수 있습니다. 이어서 `_transfer`의 멱등 처리를 빼면 무슨 일이 생길지 생각해 보세요.
2. **조건부 확인**: `ApprovalToolAgent`를 없애고, TransactionAgent의 송금 도구에 `require_confirmation=lambda amount_krw, payee, **_: ...`처럼 **함수**를 넘겨 고위험일 때만 멈추게 바꿔 보세요. 두 구조(별도 승인 에이전트 vs 조건부 확인)의 장단점을 비교해 보세요.
3. **다단계 결재**: 5,000만 원 이상은 팀장 승인 후 재무이사 승인까지 받도록 확인을 두 번 받게 바꿔 보세요. 확인 응답의 `payload`에 승인자 직급을 담아 검사할 수 있습니다.
4. **감사 로그**: 승인/거절 결정(승인자, 의견, 시각)을 `state["audit_log"]`에 남기고, 실행 끝에 출력하거나 파일로 저장해 보세요.
