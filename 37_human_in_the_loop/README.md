# ADK Human-in-the-Loop 예제 — 법인 송금 승인

Google ADK(Agent Development Kit)로 구현한 **Human-in-the-Loop(안전망) 패턴** 실습 예제입니다.
일상적인 송금은 에이전트가 바로 처리하고, 고위험 송금(한도 초과·신규 거래처)은 **실행을 실제로 멈추고 사람의 승인**을 받은 뒤에만 실행합니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다. 멈춤과 재개는 ADK의 도구 확인(Tool Confirmation) 기능으로 구현했습니다.

**Gemini · Claude · OpenAI 모두 지원합니다.** Google API 키, Claude Code에서 쓰는 Anthropic API 키, Codex에서 쓰는 OpenAI API 키 중 하나만 있으면 코드를 고치지 않고 실행됩니다(키를 자동으로 감지).

**바로 실습하려면 → [따라 하기: 설치부터 실행까지](#따라-하기-설치부터-실행까지)**

## 목차

1. [구조](#구조)
2. [의사코드를 그대로 쓰면 안 되는 이유 — 세 가지 함정](#의사코드를-그대로-쓰면-안-되는-이유--세-가지-함정)
3. [폴더 구성](#폴더-구성)
4. [**따라 하기: 설치부터 실행까지**](#따라-하기-설치부터-실행까지) ← Step 1 ~ Step 6
5. [모델 고르기 (키가 여러 개일 때)](#모델-고르기-키가-여러-개일-때)
6. [웹 UI로 실행 (`adk web`)](#웹-ui로-실행-adk-web)
7. [설정 바꾸기](#설정-바꾸기)
8. [실습 과제 아이디어](#실습-과제-아이디어)
9. [문제 해결](#문제-해결)

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

---

## 따라 하기: 설치부터 실행까지

아래 6단계를 **순서대로** 따라 하면 됩니다. 각 단계 끝의 **✅ 확인**이 맞게 나오면 다음 단계로 넘어가세요.

| 단계 | 할 일 | 한 번만 / 매번 |
|---|---|---|
| [Step 1](#step-1-가상환경-만들기) | 가상환경 만들기 | 처음 한 번 |
| [Step 2](#step-2-패키지-설치하기) | 패키지 설치하기 | 처음 한 번 |
| [Step 3](#step-3-api-키-발급받기) | API 키 발급받기 | 처음 한 번 |
| [Step 4](#step-4-api-키-설정하기) | API 키 설정하기 | 터미널을 열 때마다 (자동 설정 가능) |
| [Step 5](#step-5-실행하기) | 실행하기 | 매번 |
| [Step 6](#step-6-결과-확인하기) | 결과 확인하기 | 매번 |

### Step 1. 가상환경 만들기

이 예제 전용 파이썬 환경을 만듭니다. 기존 환경(Anaconda `base` 등)에 설치하면 다른 패키지(예: mlflow)와 버전이 충돌할 수 있으므로 **꼭 따로 만드세요.** Python 3.10 이상이 필요합니다.

```bash
cd 37_human_in_the_loop

conda deactivate                   # 프롬프트 앞에 (base)가 보이면 먼저 빠져나오기 (Anaconda 사용자만)
python3 -m venv .venv              # 가상환경 만들기 (처음 한 번)
source .venv/bin/activate          # 가상환경 켜기   (Windows: .venv\Scripts\activate)
```

✅ **확인**: 프롬프트 맨 앞에 `(.venv)`가 붙고, 아래 명령의 경로가 이 폴더의 `.venv` 안을 가리키면 성공입니다.

```bash
which python                       # …/37_human_in_the_loop/.venv/bin/python
```

> 💡 31~37번 예제를 모두 실습한다면, 폴더마다 만들지 않고 공용 환경 하나(`python3 -m venv ~/venvs/adk` → `source ~/venvs/adk/bin/activate`)를 만들어 함께 써도 됩니다.

### Step 2. 패키지 설치하기

```bash
pip install -U google-adk

# 사용할 모델에 따라 하나 더 설치 (Gemini만 쓰면 생략)
pip install -U anthropic           # Claude (Anthropic API 키)
pip install -U openai              # OpenAI GPT (OpenAI API 키)
```

| 패키지 | 용도 |
|---|---|
| `google-adk` | 에이전트 프레임워크 (2.11.0에서 확인) |
| `anthropic` / `openai` | Claude / OpenAI 모델을 쓸 때만 필요 |

✅ **확인**: 버전 번호가 출력되면 성공입니다.

```bash
python -c "import google.adk; print(google.adk.__version__)"
```

### Step 3. API 키 발급받기

**아래 셋 중 하나만** 있으면 됩니다. 이미 키가 있다면 이 단계는 건너뛰세요.

| 모델 | 키 발급 페이지 | 키 모양 |
|---|---|---|
| **Gemini** (Google) | [Google AI Studio](https://aistudio.google.com) → 로그인 → **Get API key** → **Create API key** | `AIza…` |
| **Claude** (Anthropic) | [Anthropic Console](https://console.anthropic.com) → **API Keys** → **Create Key** | `sk-ant-…` |
| **OpenAI GPT** | [OpenAI Platform](https://platform.openai.com/api-keys) → **Create new secret key** | `sk-…` |

> 💡 **Claude Code나 Codex를 이미 API 키로 쓰고 있다면** 그 키를 그대로 쓰면 됩니다 (Claude Code → `ANTHROPIC_API_KEY`, Codex → `OPENAI_API_KEY`). 터미널에서 `echo $ANTHROPIC_API_KEY` 또는 `echo $OPENAI_API_KEY`로 확인해 보세요.
>
> ⚠️ **구독 계정 로그인은 API 키가 아닙니다.** Claude Code에 Claude 구독(Pro/Max 등)으로 로그인했거나 Codex에 ChatGPT 계정으로 로그인했다면, 위 페이지에서 **API 키를 따로 발급**받아야 합니다. API 사용량은 구독과 별도로 과금됩니다.

### Step 4. API 키 설정하기

발급받은 키를 터미널에 등록합니다. **가지고 있는 키 하나만** 실행하세요.

```bash
export GOOGLE_API_KEY="AIza..."          # Gemini를 쓸 때
export ANTHROPIC_API_KEY="sk-ant-..."    # Claude를 쓸 때
export OPENAI_API_KEY="sk-..."           # OpenAI를 쓸 때
```

✅ **확인**: 키 값이 출력되면 성공입니다(빈 줄이면 설정되지 않은 것).

```bash
echo $GOOGLE_API_KEY                     # 설정한 키 이름으로 확인
```

> `export`는 **지금 열려 있는 터미널 창에서만** 유효합니다. 새 터미널을 열면 다시 설정해야 합니다.
> 매번 하기 번거로우면 `~/.zshrc`(macOS 기본) 맨 아래에 위 `export` 줄을 추가하고 `source ~/.zshrc`를 실행하세요.
> 키는 비밀번호와 같습니다. 코드나 git 저장소에 넣지 마세요.

### Step 5. 실행하기

처음에는 이 명령으로 실행해 보세요.

```bash
python adk_human_in_the_loop.py --demo
```

✅ **확인**: 실행하면 어떤 모델로 실행되는지 먼저 표시됩니다. 설정한 키에 맞는 모델이 나오면 정상입니다.

```
🧠 사용 모델: Gemini (gemini-3.8-flash)
```

다른 방법으로도 실행해 보세요.

```bash
# 1) 데모 시나리오 5개 — 승인/거절은 터미널에서 직접 입력 (수업 시연용)
python adk_human_in_the_loop.py --demo

# 2) 데모 시나리오 5개 — requests.json의 결정으로 자동 응답 (빠른 확인용)
python adk_human_in_the_loop.py --demo --auto

# 3) 직접 요청하기
python adk_human_in_the_loop.py "운영 계좌(OPS-001)에서 그린오피스 사무용품에 사무가구 2,300,000원을 송금해 줘."
```

### Step 6. 결과 확인하기

**관찰 포인트**

- 고위험 송금(시나리오 2·3·4)에서 `⏸️ 실행이 멈췄습니다` 상자가 나오고 **입력을 기다립니다**. `y`(승인) 또는 Enter(거절)를 입력하세요.
- `▶️ … 멈춘 자리에서 재개합니다` 이후 **TransactionAgent가 다시 실행되지 않는 것**을 확인하세요(재개 가능 설정 덕분).
- 거절하면 `This tool call is rejected.`가 반환되고 `📒 이번 요청으로 처리된 송금: 0건`이 됩니다.
- 시나리오 1(소액)은 멈추지 않고 바로 처리되고, 시나리오 5(잔액 부족)는 승인 요청 없이 차단됩니다.

#### 출력 예시 (시나리오 2 — 고액 송금 승인)

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

### 다음에 다시 실행할 때

Step 1~3은 다시 할 필요 없습니다. 새 터미널에서는 아래 네 줄이면 됩니다.

```bash
cd 37_human_in_the_loop
source .venv/bin/activate                # (.venv) 확인
export GOOGLE_API_KEY="..."              # ~/.zshrc에 넣어 두었다면 생략
python adk_human_in_the_loop.py --demo
```

---

## 모델 고르기 (키가 여러 개일 때)

키가 하나만 있으면 신경 쓸 필요 없습니다. 여러 개 설정되어 있으면 **Gemini → Claude → OpenAI** 순서로 자동 선택됩니다.

| 쓰는 키 | 기본 모델 | 추가 설치 |
|---|---|---|
| `GOOGLE_API_KEY` | `gemini-3.8-flash` | — |
| `ANTHROPIC_API_KEY` (Claude Code) | `claude-sonnet-5-5` | `pip install anthropic` |
| `OPENAI_API_KEY` (Codex) | `gpt-5.6` | `pip install openai` |

> 실행을 멈추고 승인받는 기능(`require_confirmation`)과 재개는 모델이 아니라 ADK가 처리하므로 **Gemini·Claude·OpenAI 어느 모델로도 똑같이 동작**합니다.

다른 것을 쓰려면 실행할 때 지정하세요.

```bash
# 공급자만 고르기 (기본 모델 사용)
ADK_PROVIDER=claude python adk_human_in_the_loop.py --demo
ADK_PROVIDER=openai python adk_human_in_the_loop.py --demo

# 모델 이름까지 직접 지정 (이름으로 공급자를 판단: claude-* → Claude, gpt-*/o* → OpenAI, 그 외 → Gemini)
ADK_MODEL=claude-opus-5-5 python adk_human_in_the_loop.py --demo
ADK_MODEL=gpt-5.6-luna    python adk_human_in_the_loop.py --demo
ADK_MODEL=gemini-3.5-flash-lite python adk_human_in_the_loop.py --demo
```

> **Claude를 Anthropic API 키로 쓸 때 주의**: ADK에 `model="claude-sonnet-5-5"`처럼 이름만 넘기면, ADK는 이것을 **Vertex AI(Google Cloud)의 Claude**로 연결해 Google Cloud 프로젝트를 요구합니다.
> 이 예제는 Anthropic API 키가 있으면 `AnthropicLlm(model=...)` 객체로 감싸서 Anthropic API로 직접 연결합니다(코드의 `resolve_model()` 참고).

## 웹 UI로 실행 (`adk web`)

```bash
mkdir -p hitl_agent
cp adk_human_in_the_loop.py hitl_agent/agent.py
cp -r data hitl_agent/data
echo "from . import agent" > hitl_agent/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > hitl_agent/.env      # 또는 ANTHROPIC_API_KEY=... / OPENAI_API_KEY=...
adk web                              # 브라우저에서 http://localhost:8000 → hitl_agent 선택
```

웹 UI에서도 도구 확인 요청 이벤트가 표시되지만, 응답 방식은 ADK 버전에 따라 다를 수 있습니다. 또 `adk web`이 이 파일의 `app`(재개 가능 설정) 대신 `root_agent`를 불러오면 위 함정 2의 재시작 동작이 나타날 수 있습니다. 멈춤과 재개를 정확히 관찰하려면 **명령행 실행을 권장**합니다.

> `adk web`은 에이전트 폴더의 `.env` 파일에서 키를 읽습니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

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

## 실습 과제 아이디어

1. **함정 직접 확인하기**: `main()`의 `InMemoryRunner(app=app)`를 `InMemoryRunner(agent=workflow, app_name=APP_NAME)`로 바꿔 시나리오 2를 실행해 보세요. 승인 후 TransactionAgent가 다시 도는 것을 확인할 수 있습니다. 이어서 `_transfer`의 멱등 처리를 빼면 무슨 일이 생길지 생각해 보세요.
2. **조건부 확인**: `ApprovalToolAgent`를 없애고, TransactionAgent의 송금 도구에 `require_confirmation=lambda amount_krw, payee, **_: ...`처럼 **함수**를 넘겨 고위험일 때만 멈추게 바꿔 보세요. 두 구조(별도 승인 에이전트 vs 조건부 확인)의 장단점을 비교해 보세요.
3. **다단계 결재**: 5,000만 원 이상은 팀장 승인 후 재무이사 승인까지 받도록 확인을 두 번 받게 바꿔 보세요. 확인 응답의 `payload`에 승인자 직급을 담아 검사할 수 있습니다.
4. **감사 로그**: 승인/거절 결정(승인자, 의견, 시각)을 `state["audit_log"]`에 남기고, 실행 끝에 출력하거나 파일로 저장해 보세요.

## 문제 해결

**설치·환경 (Step 1~2)**

| 증상 | 원인과 해결 |
|---|---|
| `pip's dependency resolver ... incompatible` (예: `mlflow ... requires starlette<1`) | 기존 환경(Anaconda `base` 등)에 설치해서 다른 패키지와 충돌. `conda deactivate` 후 [Step 1](#step-1-가상환경-만들기)대로 **가상환경을 따로 만들어** 설치 |
| 프롬프트에 `(.venv)`가 없음 / `which python`이 `/opt/anaconda3/...` | 가상환경이 꺼져 있음. 이 폴더에서 `source .venv/bin/activate` |
| `ModuleNotFoundError: google.adk` | 가상환경을 켜지 않았거나 설치 전. `source .venv/bin/activate` 후 `pip install -U google-adk` |
| `Claude를 쓰려면 anthropic 패키지가 필요합니다` / `OpenAI 모델을 쓰려면 openai 패키지가 필요합니다` | `pip install -U anthropic` / `pip install -U openai` |

**API 키 (Step 3~4)**

| 증상 | 원인과 해결 |
|---|---|
| `API 키가 설정되어 있지 않습니다` | `echo $GOOGLE_API_KEY $ANTHROPIC_API_KEY $OPENAI_API_KEY`로 현재 터미널에 키가 있는지 확인. 새 터미널을 열었다면 `export`를 다시 하거나 `~/.zshrc`에 등록 |
| `❌ API 키 인증 실패` (`Unauthorized`, `401`) | 키 값 오타, 만료된 키, 또는 **구독 로그인 정보를 키로 착각**한 경우. [Step 3](#step-3-api-키-발급받기)의 페이지에서 API 키를 새로 발급 |
| 의도와 다른 공급자가 선택됨 | 키가 여러 개 설정됨. `ADK_PROVIDER=claude`처럼 직접 지정 ([모델 고르기](#모델-고르기-키가-여러-개일-때)) |

**실행 중 (Step 5~6)**

| 증상 | 원인과 해결 |
|---|---|
| `404 ... model not found` / `model_not_found` | 계정에서 쓸 수 없는 모델 이름. 각 공급자의 모델 목록에서 확인해 `ADK_MODEL`로 지정 |
| `400 … Function tools with reasoning_effort are not supported … use /v1/responses` (OpenAI) | 이전 버전 코드에서 OpenAI를 예전 Chat Completions 방식으로 연결해서 생긴 오류. 최신 코드는 Responses API(`OpenAIResponsesLlm`)로 연결하므로 코드 파일을 최신으로 바꾸면 해결 |
| `503 UNAVAILABLE` / `high demand` / `⏳ 모델 서버가 일시적으로 응답하지 못했습니다` | 코드 문제가 아니라 모델 서버의 일시적 과부하. Gemini는 자동으로 최대 6번(약 1분) 재시도하며, 그래도 실패하면 이 안내가 나옴. 1~2분 뒤 다시 실행하거나 `ADK_MODEL=gemini-3.5-flash-lite`처럼 가벼운 모델, 또는 `ADK_PROVIDER=claude`/`openai`로 다른 공급자 사용 |
| 고액인데 승인 없이 끝남 | 정책상 '차단'(잔액 부족 등)일 수 있음. `check_policy` 결과(↳ 줄) 확인 |
| 승인 후 TransactionAgent가 또 실행됨 | `App(..., resumability_config=ResumabilityConfig(is_resumable=True))` 없이 실행한 경우 (`adk web` 포함) |
| `ApprovalToolAgent`가 대기 건을 못 찾음 | TransactionAgent가 `request_approval`을 호출하지 않음. 더 강한 모델을 쓰거나 instruction 강조 |
