# ADK Coordinator/Dispatcher 예제 — 고객 지원 라우팅

Google ADK(Agent Development Kit)로 구현한 **Coordinator/Dispatcher(컨시어지) 패턴** 실습 예제입니다.
코디네이터 에이전트가 고객 문의의 의도를 분석해 **청구 전문가** 또는 **기술 지원 전문가**에게 대화를 넘깁니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다.

**Gemini · Claude · OpenAI 모두 지원합니다.** Google API 키, Claude Code에서 쓰는 Anthropic API 키, Codex에서 쓰는 OpenAI API 키 중 하나만 있으면 코드를 고치지 않고 실행됩니다(키를 자동으로 감지).

**바로 실습하려면 → [따라 하기: 설치부터 실행까지](#따라-하기-설치부터-실행까지)**

## 목차

1. [구조](#구조)
2. [폴더 구성](#폴더-구성)
3. [**따라 하기: 설치부터 실행까지**](#따라-하기-설치부터-실행까지) ← Step 1 ~ Step 6
4. [모델 고르기 (키가 여러 개일 때)](#모델-고르기-키가-여러-개일-때)
5. [웹 UI로 실행 (`adk web`)](#웹-ui로-실행-adk-web)
6. [설정 바꾸기](#설정-바꾸기)
7. [실습 과제 아이디어](#실습-과제-아이디어)
8. [문제 해결](#문제-해결)

## 구조

```
                         ┌─ transfer_to_agent ─▶ BillingSpecialist ──▶ get_customer / list_invoices
사용자 ─▶ CoordinatorAgent ┤                       (청구·결제·환불)      get_invoice / request_refund
         (의도 분석·위임)  │                                                     │
                         └─ transfer_to_agent ─▶ TechSupportSpecialist ─▶ check_service_status
                                                 (장애·오류·버그)        lookup_error_code / search_known_issues
                                                            │
                         ◀──── 담당이 아닌 질문은 코디네이터로 되돌려 보냄 ────┘
```

| 에이전트 | 역할 | 도구 (블로그 이름) | 조회 데이터 |
|---|---|---|---|
| `CoordinatorAgent` | 의도를 분석해 위임. 직접 답하지 않음 | `transfer_to_agent` (ADK가 자동 추가) | — |
| `BillingSpecialist` | 요금·청구서·결제 실패·환불 | `get_customer`, `list_invoices`, `get_invoice`, `request_refund` (BillingSystemDB) | `data/billing_db.json` |
| `TechSupportSpecialist` | 서비스 장애·오류 코드·버그 | `check_service_status`, `lookup_error_code`, `search_known_issues` (DiagnosticTool) | `data/diagnostics_kb.json` |

**핵심 포인트**

- **`sub_agents`**: 코디네이터에 전문가들을 등록하면, ADK의 AutoFlow가 `transfer_to_agent` 도구를 자동으로 붙여 줍니다. 코디네이터 LLM이 이 도구를 호출하면 대화가 해당 전문가에게 넘어갑니다.
- **`description` = 라우팅 LLM이 읽는 API 문서**: 코디네이터는 각 전문가의 `description`을 보고 누구에게 넘길지 고릅니다. 담당 범위를 구체적으로, 서로 겹치지 않게 써야 라우팅이 정확해집니다.
- **위임 후 대화 유지**: 넘겨받은 전문가가 같은 세션의 다음 질문도 이어서 처리합니다. 담당이 아닌 질문이 오면 다시 코디네이터(부모)로 넘겨 재라우팅합니다.
- **Sequential Pipeline과의 차이**: 순서가 고정된 조립 라인과 달리, 어느 에이전트가 실행될지는 **실행 중에 LLM이 결정**합니다.

## 폴더 구성

```
32_adk_dispatcher/
├── adk_coordinator_dispatcher.py   # 이 예제의 핵심: 코디네이터 + 전문가 2명 + 대화/데모 실행
├── support_tools.py                # 상담 도구: 청구 조회·환불 4개, 장애 진단 3개 (data/*.json 조회)
├── model_config.py                 # API 키에 맞춰 Gemini / Claude / OpenAI 모델 자동 선택 (resolve_model)
├── error_messages.py               # 서버 과부하·요청 한도 같은 일시적 오류 안내 문구
├── tests/                          # 동작 고정용 테스트 (pytest, 네트워크·API 키 불필요)
├── README.md
└── data/
    ├── billing_db.json             # 가상의 청구 시스템: 고객 3명, 청구서 4건, 환불 정책
    ├── diagnostics_kb.json         # 가상의 진단 자료: 서비스 상태 5종, 오류 코드 5종, 알려진 이슈 2건
    └── demo_scenarios.json         # --demo [번호] 로 자동 실행할 상담 시나리오 4개
```

데이터는 모두 가상의 클라우드 서비스 "Acme Cloud" 기준입니다. 상담 실습에 쓸 만한 상황을 일부러 넣어 두었습니다.

| 데이터 | 들어 있는 상황 |
|---|---|
| `C-1001` / `INV-2026-1101` | 10월 청구서에 **플랜 요금이 두 번 청구**됨 (정책상 환불 대상) |
| `C-1003` / `INV-2026-1103` | 카드 결제 3회 실패로 **계정 일시 정지** |
| `storage` 서비스 | 서울 리전(ap-northeast-2) **업로드 지연 장애** 진행 중 |
| `E504` + 알려진 이슈 `KI-311` | 대용량 업로드 시간 초과, 우회 방법과 해결 예정 시각 |
| `E429` | 요금제별 분당 요청 한도 초과 |

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
cd 32_adk_dispatcher

conda deactivate                   # 프롬프트 앞에 (base)가 보이면 먼저 빠져나오기 (Anaconda 사용자만)
python3 -m venv .venv              # 가상환경 만들기 (처음 한 번)
source .venv/bin/activate          # 가상환경 켜기   (Windows: .venv\Scripts\activate)
```

✅ **확인**: 프롬프트 맨 앞에 `(.venv)`가 붙고, 아래 명령의 경로가 이 폴더의 `.venv` 안을 가리키면 성공입니다.

```bash
which python                       # …/32_adk_dispatcher/.venv/bin/python
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
python adk_coordinator_dispatcher.py --demo
```

✅ **확인**: 실행하면 어떤 모델로 실행되는지 먼저 표시됩니다. 설정한 키에 맞는 모델이 나오면 정상입니다.

```
🧠 사용 모델: Gemini (gemini-3.8-flash)
```

대화형으로 직접 상담해 볼 수도 있습니다.

```bash
python adk_coordinator_dispatcher.py          # 대화형 상담 (종료: quit)
```

### Step 6. 결과 확인하기

**관찰 포인트**

- `↪ [CoordinatorAgent] → BillingSpecialist 에게 위임` 줄에서 **누가 누구에게 넘겼는지** 볼 수 있습니다. 코디네이터는 직접 답하지 않고 넘기기만 합니다.
- 시나리오 1의 두 번째 질문은 코디네이터를 **거치지 않고** BillingSpecialist가 바로 받습니다(위임 후 대화 유지).
- 시나리오 3에서는 TechSupport가 결제 질문을 받자 **Coordinator로 되돌려 보내고**, Coordinator가 다시 Billing에게 넘깁니다.
- 시나리오 4(인사만 한 경우)는 위임 없이 코디네이터가 청구/기술 중 무엇인지 되묻습니다.

#### 1) 데모 시나리오 자동 실행

```bash
python adk_coordinator_dispatcher.py --demo          # 시나리오 3번만 실행 (기본)
python adk_coordinator_dispatcher.py --demo 1        # 시나리오 1번만 실행
python adk_coordinator_dispatcher.py --demo 2 4      # 시나리오 2번, 4번 실행
python adk_coordinator_dispatcher.py --demo all      # 시나리오 4개 모두 실행
```

`--demo`만 쓰면 재라우팅(되돌려 보내기)이 가장 잘 보이는 **시나리오 3번만** 실행합니다.
다른 시나리오는 `--demo` 뒤에 번호를 붙이세요. 시나리오마다 새 세션에서 시작합니다.
기본 번호는 코드의 `DEFAULT_DEMO`에서 바꿀 수 있습니다.

| 시나리오 | 기대하는 흐름 |
|---|---|
| 1. 중복 청구 확인과 환불 | Coordinator → **Billing**. 청구서 조회 후 두 번째 턴에서 환불 접수 (코디네이터를 다시 거치지 않음) |
| 2. 업로드 E504 오류 | Coordinator → **TechSupport**. 오류 코드·storage 상태·알려진 이슈 조회 |
| 3. 기술 문의 → 청구 문의로 전환 | TechSupport가 응대하다가 "계정 정지·결제" 질문에 **Coordinator로 되돌려 보내고** Billing이 이어받음 |
| 4. 의도 불분명 ("문의 좀 하려고요") | Coordinator가 위임하지 않고 청구/기술 중 무엇인지 되물음 |

출력 예시 (위임과 도구 호출이 표시됩니다):

```
======================================================================
▶ 시나리오: 3. 주제 전환 — 기술 문의 후 청구 문의
======================================================================

🙋 사용자: API를 호출하면 E429가 떠요. 고객 ID는 C-1003이에요.
   ↪ [CoordinatorAgent] → TechSupportSpecialist 에게 위임
   🔧 [TechSupportSpecialist] 도구 호출: lookup_error_code({"code": "E429"})

🤖 TechSupportSpecialist:
(요청 한도 초과의 원인과 조치 방법 …)

🙋 사용자: 그런데 제 계정이 정지됐다고 나오는데 결제 문제인가요?
   ↪ [TechSupportSpecialist] → CoordinatorAgent 에게 위임
   ↪ [CoordinatorAgent] → BillingSpecialist 에게 위임
   🔧 [BillingSpecialist] 도구 호출: get_customer({"customer_id": "C-1003"})

🤖 BillingSpecialist:
(결제 실패로 인한 정지 안내 …)
```

> 답변 문장과 도구 호출 순서는 LLM이 정하므로 실행할 때마다 조금씩 달라질 수 있습니다.
> 예를 들어 전문가가 도구를 한 번에 여러 개 호출하거나, 고객 ID를 먼저 되묻기도 합니다.
#### 2) 대화형 상담

```bash
python adk_coordinator_dispatcher.py
```

```
Acme Cloud 고객 지원입니다. 무엇을 도와드릴까요? (종료: quit)
🙋 사용자: 고객 ID C-1001인데 이번 달 청구서 금액이 이상해요
```

한 세션 안에서 대화가 이어지므로, 청구 질문 → 기술 질문 → 다시 청구 질문처럼 주제를 바꿔 가며 재라우팅을 관찰해 보세요.
`quit`(또는 `exit`, `종료`, Ctrl+D)로 끝냅니다.

### 다음에 다시 실행할 때

Step 1~3은 다시 할 필요 없습니다. 새 터미널에서는 아래 네 줄이면 됩니다.

```bash
cd 32_adk_dispatcher
source .venv/bin/activate                # (.venv) 확인
export GOOGLE_API_KEY="..."              # ~/.zshrc에 넣어 두었다면 생략
python adk_coordinator_dispatcher.py --demo
```

---

## 모델 고르기 (키가 여러 개일 때)

키가 하나만 있으면 신경 쓸 필요 없습니다. 여러 개 설정되어 있으면 **Gemini → Claude → OpenAI** 순서로 자동 선택됩니다.

| 쓰는 키 | 기본 모델 | 추가 설치 |
|---|---|---|
| `GOOGLE_API_KEY` | `gemini-3.8-flash` | — |
| `ANTHROPIC_API_KEY` (Claude Code) | `claude-sonnet-5-5` | `pip install anthropic` |
| `OPENAI_API_KEY` (Codex) | `gpt-5.6` | `pip install openai` |

다른 것을 쓰려면 실행할 때 지정하세요.

```bash
# 공급자만 고르기 (기본 모델 사용)
ADK_PROVIDER=claude python adk_coordinator_dispatcher.py --demo
ADK_PROVIDER=openai python adk_coordinator_dispatcher.py --demo

# 모델 이름까지 직접 지정 (이름으로 공급자를 판단: claude-* → Claude, gpt-*/o* → OpenAI, 그 외 → Gemini)
ADK_MODEL=claude-opus-5-5 python adk_coordinator_dispatcher.py --demo
ADK_MODEL=gpt-5.6-luna    python adk_coordinator_dispatcher.py --demo
ADK_MODEL=gemini-3.5-flash-lite python adk_coordinator_dispatcher.py --demo
```

> **Claude를 Anthropic API 키로 쓸 때 주의**: ADK에 `model="claude-sonnet-5-5"`처럼 이름만 넘기면, ADK는 이것을 **Vertex AI(Google Cloud)의 Claude**로 연결해 Google Cloud 프로젝트를 요구합니다.
> 이 예제는 Anthropic API 키가 있으면 `AnthropicLlm(model=...)` 객체로 감싸서 Anthropic API로 직접 연결합니다(`model_config.py`의 `resolve_model()` 참고).

## 웹 UI로 실행 (`adk web`)

ADK 개발 UI에서는 어떤 에이전트가 응답했는지, 이벤트와 상태가 어떻게 바뀌는지 그래프로 볼 수 있습니다.

```bash
mkdir -p support_dispatcher
# 코드가 여러 파일로 나뉘어 있으므로 복사하지 않고, 예제 폴더의 root_agent를 불러오는 agent.py를 만듭니다.
cat > support_dispatcher/agent.py <<'EOF'
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 예제 폴더(32_adk_dispatcher)
from adk_coordinator_dispatcher import root_agent  # noqa: E402,F401
EOF
echo "from . import agent" > support_dispatcher/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > support_dispatcher/.env      # 또는 ANTHROPIC_API_KEY=... / OPENAI_API_KEY=...
adk web                              # 브라우저에서 http://localhost:8000 → support_dispatcher 선택
```

> `adk web`은 에이전트 폴더의 `.env` 파일에서 키를 읽습니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 모델 공급자 | `export ADK_PROVIDER=gemini` / `claude` / `openai` | 설정된 키로 자동 감지 |
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` (또는 `claude-opus-5-5`, `gpt-5.6-luna` …) | 공급자별 기본 모델 |
| 공급자별 기본 모델 | `model_config.py`의 `DEFAULT_MODELS` | Gemini `gemini-3.8-flash` · Claude `claude-sonnet-5-5` · OpenAI `gpt-5.6` |
| 고객·청구서 데이터 | `data/billing_db.json` 수정 | 고객 3명, 청구서 4건 |
| 오류 코드·장애 정보 | `data/diagnostics_kb.json` 수정 | 오류 코드 5종 |
| 데모 시나리오 | `data/demo_scenarios.json`의 `turns`에 질문 추가 | 시나리오 4개 |
| `--demo`만 쓸 때 실행할 시나리오 | `adk_coordinator_dispatcher.py`의 `DEFAULT_DEMO` | `[3]` |

> `request_refund`(`support_tools.py`)는 접수 내역을 **세션 상태(`session.state["refund_tickets"]`)에만** 기록하며 JSON 파일은 바꾸지 않습니다.
> 그래서 프로그램을 다시 실행하면 데이터가 항상 처음 상태로 돌아갑니다.

## 실습 과제 아이디어

1. **전문가 추가**: 요금제 변경·신규 가입을 담당하는 `SalesSpecialist`를 만들어 `sub_agents`에 추가하고, 코디네이터 instruction의 분류 기준도 고쳐 보세요.
2. **description 실험**: `BillingSpecialist`의 description을 일부러 모호하게 바꾼 뒤 라우팅이 어떻게 흔들리는지 관찰해 보세요.
3. **되돌려 보내기 막기**: 전문가에 `disallow_transfer_to_parent=True`를 설정하면 시나리오 3이 어떻게 달라지는지 비교해 보세요.
4. **Human-in-the-Loop 결합**: 일정 금액 이상의 환불은 바로 접수하지 않고 담당자 승인을 받도록 `support_tools.py`의 `request_refund`를 바꿔 보세요.

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
| `FileNotFoundError: .../data/billing_db.json` | `data/` 폴더가 스크립트와 같은 위치에 있어야 함 (`adk web`용 폴더에도 복사) |
| 엉뚱한 전문가에게 넘어감 | 각 전문가의 `description`을 더 구체적으로 쓰고, 코디네이터 `instruction`에 분류 기준을 추가 |
| 코디네이터가 직접 답해 버림 | 코디네이터 `instruction`의 "직접 답을 만들지 말고 transfer_to_agent로 넘기라"는 문장을 강조하거나, 더 강한 모델 사용 |
