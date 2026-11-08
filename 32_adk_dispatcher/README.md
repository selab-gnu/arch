# ADK Coordinator/Dispatcher 예제 — 고객 지원 라우팅

Google ADK(Agent Development Kit)로 구현한 **Coordinator/Dispatcher(컨시어지) 패턴** 실습 예제입니다.
코디네이터 에이전트가 고객 문의의 의도를 분석해 **청구 전문가** 또는 **기술 지원 전문가**에게 대화를 넘깁니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다.

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
├── adk_coordinator_dispatcher.py   # 이 예제
├── README.md
└── data/
    ├── billing_db.json             # 가상의 청구 시스템: 고객 3명, 청구서 4건, 환불 정책
    ├── diagnostics_kb.json         # 가상의 진단 자료: 서비스 상태 5종, 오류 코드 5종, 알려진 이슈 2건
    └── demo_scenarios.json         # --demo 로 자동 실행할 상담 시나리오 4개
```

데이터는 모두 가상의 클라우드 서비스 "Acme Cloud" 기준입니다. 상담 실습에 쓸 만한 상황을 일부러 넣어 두었습니다.

| 데이터 | 들어 있는 상황 |
|---|---|
| `C-1001` / `INV-2026-1101` | 10월 청구서에 **플랜 요금이 두 번 청구**됨 (정책상 환불 대상) |
| `C-1003` / `INV-2026-1103` | 카드 결제 3회 실패로 **계정 일시 정지** |
| `storage` 서비스 | 서울 리전(ap-northeast-2) **업로드 지연 장애** 진행 중 |
| `E504` + 알려진 이슈 `KI-311` | 대용량 업로드 시간 초과, 우회 방법과 해결 예정 시각 |
| `E429` | 요금제별 분당 요청 한도 초과 |

## 설치

Python 3.10 이상이 필요합니다.

```bash
cd 32_adk_dispatcher
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -U google-adk
```

## API 키 설정

**방법 A — Google AI Studio (간단)**

[Google AI Studio](https://aistudio.google.com)에서 API 키를 발급받은 뒤:

```bash
export GOOGLE_API_KEY="발급받은_키"
```

**방법 B — Vertex AI (Google Cloud)**

```bash
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="내-프로젝트-ID"
export GOOGLE_CLOUD_LOCATION="us-central1"
gcloud auth application-default login
```

> `python`으로 직접 실행할 때는 위처럼 터미널에서 export해야 합니다.
> `adk web` / `adk run`으로 실행할 때는 에이전트 폴더의 `.env` 파일을 자동으로 읽습니다(아래 참고). 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 실행

### 1) 데모 시나리오 자동 실행

```bash
python adk_coordinator_dispatcher.py --demo
```

`data/demo_scenarios.json`의 시나리오 4개를 차례로 실행합니다(시나리오마다 새 세션).

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

### 2) 대화형 상담

```bash
python adk_coordinator_dispatcher.py
```

```
Acme Cloud 고객 지원입니다. 무엇을 도와드릴까요? (종료: quit)
🙋 사용자: 고객 ID C-1001인데 이번 달 청구서 금액이 이상해요
```

한 세션 안에서 대화가 이어지므로, 청구 질문 → 기술 질문 → 다시 청구 질문처럼 주제를 바꿔 가며 재라우팅을 관찰해 보세요.
`quit`(또는 `exit`, `종료`, Ctrl+D)로 끝냅니다.

### 3) 웹 UI로 실행 (`adk web`)

ADK 개발 UI에서는 어떤 에이전트가 응답했는지, 이벤트와 상태가 어떻게 바뀌는지 그래프로 볼 수 있습니다.

```bash
mkdir -p support_dispatcher
cp adk_coordinator_dispatcher.py support_dispatcher/agent.py
cp -r data support_dispatcher/data
echo "from . import agent" > support_dispatcher/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > support_dispatcher/.env
adk web                              # 브라우저에서 http://localhost:8000 → support_dispatcher 선택
```

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` | `gemini-3.8-flash` |
| 고객·청구서 데이터 | `data/billing_db.json` 수정 | 고객 3명, 청구서 4건 |
| 오류 코드·장애 정보 | `data/diagnostics_kb.json` 수정 | 오류 코드 5종 |
| 데모 시나리오 | `data/demo_scenarios.json`의 `turns`에 질문 추가 | 시나리오 4개 |

> `request_refund`는 접수 내역을 **세션 상태(`session.state["refund_tickets"]`)에만** 기록하며 JSON 파일은 바꾸지 않습니다.
> 그래서 프로그램을 다시 실행하면 데이터가 항상 처음 상태로 돌아갑니다.

## 문제 해결

| 증상 | 원인과 해결 |
|---|---|
| `ModuleNotFoundError: google.adk` | 가상환경을 활성화했는지 확인하고 `pip install -U google-adk` |
| API 키·인증 관련 오류 | `echo $GOOGLE_API_KEY`로 현재 터미널에 키가 설정되어 있는지 확인 |
| `404 ... model not found` | 사용 가능한 모델 ID로 `ADK_MODEL` 변경 (Google AI Studio의 모델 목록 참고) |
| `FileNotFoundError: .../data/billing_db.json` | `data/` 폴더가 스크립트와 같은 위치에 있어야 함 (`adk web`용 폴더에도 복사) |
| 엉뚱한 전문가에게 넘어감 | 각 전문가의 `description`을 더 구체적으로 쓰고, 코디네이터 `instruction`에 분류 기준을 추가 |
| 코디네이터가 직접 답해 버림 | 코디네이터 `instruction`의 "직접 답을 만들지 말고 transfer_to_agent로 넘기라"는 문장을 강조하거나, 더 강한 모델 사용 |

## 실습 과제 아이디어

1. **전문가 추가**: 요금제 변경·신규 가입을 담당하는 `SalesSpecialist`를 만들어 `sub_agents`에 추가하고, 코디네이터 instruction의 분류 기준도 고쳐 보세요.
2. **description 실험**: `BillingSpecialist`의 description을 일부러 모호하게 바꾼 뒤 라우팅이 어떻게 흔들리는지 관찰해 보세요.
3. **되돌려 보내기 막기**: 전문가에 `disallow_transfer_to_parent=True`를 설정하면 시나리오 3이 어떻게 달라지는지 비교해 보세요.
4. **Human-in-the-Loop 결합**: 일정 금액 이상의 환불은 바로 접수하지 않고 담당자 승인을 받도록 `request_refund`를 바꿔 보세요.
