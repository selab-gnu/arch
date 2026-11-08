# ADK Generator & Critic 예제 — 자연어 → SQL 생성·검증 루프

Google ADK(Agent Development Kit)로 구현한 **Generator & Critic(편집자 책상) 패턴** 실습 예제입니다.
Generator가 자연어 질문을 SQL로 바꾸면 Critic이 **실제로 실행해 보고** 판정합니다. 통과(`PASS`)할 때까지 피드백을 반영해 다시 작성하는 루프를 돕니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다. (루프 종료 방식은 아래 설명처럼 바꿨습니다.)

**Gemini · Claude · OpenAI 모두 지원합니다.** Claude Code에서 쓰는 Anthropic API 키나 Codex에서 쓰는 OpenAI API 키가 터미널에 설정되어 있으면, 코드를 고치지 않고 그대로 실행됩니다(키를 자동으로 감지). → [API 키 설정](#api-키-설정)

## 구조

```
ValidationLoop (LoopAgent, max_iterations=5)
 ┌──────────────────────────────────────────────────────────────────────────┐
 │ ① Generator   질문 + 스키마 + {feedback?}  ──▶  SQL 초안      → state["draft"]   │
 │ ② Critic      validate_sql 도구로 실제 실행 ──▶  PASS / FAIL: … → state["feedback"]│
 │ ③ ExitConditionChecker(condition_key="feedback", exit_condition="PASS")     │
 │               feedback이 PASS면 escalate ──▶ 루프 종료                          │
 └──────────────── PASS가 아니면 ①로 돌아가 피드백을 반영해 다시 작성 ──────────────────┘
```

| 단계 | 에이전트 | 하는 일 | 상태 키 |
|---|---|---|---|
| ① | `Generator` (LLM) | 질문을 SQLite `SELECT` 문으로 작성. 두 번째 바퀴부터는 Critic의 지적을 반영 | `draft` |
| ② | `Critic` (LLM) | `validate_sql` 도구로 초안을 실제 DB에서 실행 → 오류가 없으면 질문에 맞는지까지 확인 | `feedback` |
| ③ | `ExitConditionChecker` (일반 코드) | `feedback`이 `PASS`로 시작하면 루프를 멈춤 | — |

**핵심 포인트**

- **생성과 평가의 분리**: 같은 LLM에게 "작성하고 스스로 검토하라"고 하는 것보다, 역할을 나누고 평가자에게 **실행 도구**를 주는 편이 훨씬 신뢰할 만합니다.
- **조건부 루프**: `LoopAgent`는 하위 에이전트를 순서대로 반복 실행합니다. 하위 에이전트가 `escalate`를 내거나 `max_iterations`에 도달하면 멈춥니다.
- **상태로 주고받는 피드백**: Critic의 결과(`output_key="feedback"`)가 다음 바퀴 Generator의 instruction `{feedback?}` 자리에 자동으로 들어갑니다.
- **Iterative Refinement와의 차이**: 이 패턴은 **맞다/틀리다(정확성)**를 판정해 통과하면 끝납니다. Iterative Refinement는 **더 좋게(품질)** 다듬는 것이 목적입니다.

## 블로그 의사코드와 다른 점

| 의사코드 | 이 예제 | 이유 |
|---|---|---|
| `LoopAgent(..., condition_key="feedback", exit_condition="PASS")` | `ExitConditionChecker(condition_key="feedback", exit_condition="PASS")`를 루프의 마지막 하위 에이전트로 추가 | ADK의 `LoopAgent`에는 `condition_key` / `exit_condition` 인자가 **없습니다**(넣으면 검증 오류). 루프를 끝내는 공식 방법은 하위 에이전트의 `escalate` 이벤트와 `max_iterations`뿐이라, 같은 이름의 인자를 받는 작은 코드 에이전트로 구현했습니다. |
| `{feedback}` | `{feedback?}` | 첫 바퀴에는 `feedback`이 아직 없어서 `{feedback}`이면 `Context variable not found` 오류가 납니다. `?`를 붙이면 없을 때 빈 문자열이 됩니다. |
| (반복 횟수 제한 없음) | `max_iterations=5` | PASS가 영영 나오지 않을 때 무한 반복과 비용 폭증을 막는 안전장치입니다. |
| Critic이 눈으로 검사 | Critic에 `validate_sql` 도구 | 문법·컬럼 오류는 SQLite가 확정적으로 판정하고, LLM은 "질문에 맞는가"만 판단합니다. |

> 참고: ADK 2.x에서 `LoopAgent`는 **deprecated**로 표시되어 있습니다(그래프 기반 `Workflow`로 대체 예정). 아직 정상 동작하고, `Workflow`는 LlmAgent의 하위 에이전트로 쓸 수 없어 이 예제는 `LoopAgent`를 사용합니다. 경고 메시지는 코드에서 숨겼습니다.

## 폴더 구성

```
35_adk_generator_critic/
├── adk_generator_critic.py   # 이 예제
├── README.md
└── data/
    ├── shop_schema.sql       # 가상 온라인 쇼핑몰 DB (테이블 4개 + 샘플 데이터)
    └── questions.json        # 자연어 질문 8개 (쉬움 2 · 보통 3 · 어려움 3) + 채점용 정답 SQL
```

### 실습 DB (`data/shop_schema.sql`)

`customers`(8명) · `products`(10개) · `orders`(12건) · `order_items`로 이루어진 가상 쇼핑몰입니다.
실행할 때마다 **메모리에 새로 만들기 때문에** 원본 파일이나 데이터가 바뀌지 않습니다.

컬럼 이름을 일부러 흔한 이름과 다르게 지었습니다. LLM이 흔히 지어내는 이름을 쓰면 Critic이 오류를 잡아 되돌려 보내는 장면을 볼 수 있습니다.

| LLM이 흔히 지어내는 이름 | 실제 컬럼 |
|---|---|
| `name` | `cust_name`, `prod_name` |
| `order_date`, `created_at` | `ordered_at` |
| `price` | `unit_price_krw` |
| `quantity` | `qty` |

함정도 몇 가지 넣었습니다. 단종 상품(`is_active = 0`), 취소·환불 주문(`status`), 주문이 없는 고객 등은 질문을 꼼꼼히 읽어야 정답이 나옵니다.

### 문제 (`data/questions.json`)

| # | 난이도 | 질문 |
|---|---|---|
| 1 | 쉬움 | 서울에 사는 고객의 이름과 등급을 가입일 순서로 |
| 2 | 쉬움 | 현재 판매 중인 전자제품을 가격이 비싼 순으로 |
| 3 | 보통 | 2026년 10월 주문 수를 상태별로 |
| 4 | 보통 | 고객별 총 구매 금액 (취소·환불 제외) |
| 5 | 보통 | 카테고리별 판매 수량 합계 (취소·환불 제외) |
| 6 | 어려움 | 한 번도 주문하지 않은 고객 |
| 7 | 어려움 | VIP 고객이 산 상품 중 가장 많이 팔린 3개 |
| 8 | 어려움 | 단종된 상품이 들어 있는 주문 |

`expected_sql`은 **채점용**이며 에이전트에게는 보여 주지 않습니다. 컬럼 이름이나 순서가 달라도 결과 값이 같으면 정답으로 칩니다.

## 설치

Python 3.10 이상이 필요합니다. SQLite는 파이썬에 기본 내장되어 있어 따로 설치할 필요가 없습니다.

```bash
cd 35_adk_generator_critic
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

### Claude Code · Codex를 쓰고 있다면

이미 Claude Code나 Codex를 **API 키로** 쓰고 있다면, 그 키가 들어 있는 터미널에서 바로 실행하면 됩니다.

```bash
echo $ANTHROPIC_API_KEY     # Claude Code용 키가 보이면 → Claude로 실행됨
echo $OPENAI_API_KEY        # Codex용 키가 보이면     → OpenAI로 실행됨
python adk_generator_critic.py all
```

> **구독 계정으로 로그인해서 쓰는 경우는 해당되지 않습니다.**
> Claude Code에 Claude 구독(Pro/Max 등)으로 로그인했거나, Codex에 ChatGPT 계정으로 로그인했다면, 이 로그인 정보는 API 키가 아니어서 이 프로그램에서 쓸 수 없습니다.
> 이때는 [Anthropic Console](https://console.anthropic.com) 또는 [OpenAI Platform](https://platform.openai.com/api-keys)에서 **API 키를 따로 발급**받아 위처럼 설정하세요. API 사용량은 구독과 별도로 과금됩니다.

### 키가 여러 개일 때 / 모델을 직접 고를 때

자동 감지 순서는 **Gemini → Claude → OpenAI**입니다. 다른 것을 쓰려면 지정하세요.

```bash
# 공급자만 고르기 (기본 모델 사용)
ADK_PROVIDER=claude python adk_generator_critic.py all
ADK_PROVIDER=openai python adk_generator_critic.py all

# 모델 이름까지 직접 지정 (이름으로 공급자를 판단: claude-* → Claude, gpt-*/o* → OpenAI, 그 외 → Gemini)
ADK_MODEL=claude-opus-5-5 python adk_generator_critic.py all
ADK_MODEL=gpt-5.6-luna    python adk_generator_critic.py all
```

> **Claude를 Anthropic API 키로 쓸 때 주의**: ADK에 `model="claude-sonnet-5-5"`처럼 이름만 넘기면, ADK는 이것을 **Vertex AI(Google Cloud)의 Claude**로 연결해 Google Cloud 프로젝트를 요구합니다.
> 이 예제는 Anthropic API 키가 있으면 `AnthropicLlm(model=...)` 객체로 감싸서 Anthropic API로 직접 연결합니다(코드의 `resolve_model()` 참고).

> `python`으로 직접 실행할 때는 위처럼 터미널에서 export해야 합니다. `adk web`은 에이전트 폴더의 `.env` 파일에 키를 적으면 읽습니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 실행

```bash
# 1) 문제 목록 보기
python adk_generator_critic.py

# 2) 특정 문제 풀기
python adk_generator_critic.py 4

# 3) 8문제 모두 풀고 채점
python adk_generator_critic.py all

# 4) 직접 질문하기
python adk_generator_critic.py "등급별 고객 수를 보여 줘"

# 5) 최대 반복 횟수 바꾸기 (기본 5)
MAX_ITERATIONS=2 python adk_generator_critic.py 7
```

### 출력 예시

바퀴마다 Generator의 초안과 Critic의 판정이 표시됩니다.

```
======================================================================
▶ 질문 #4 (보통): 고객별 총 구매 금액을 구해서 많은 순으로 보여 줘. 취소되거나 환불된 주문은 빼 줘.
======================================================================

  ── 반복 1 ──
  ✍️  Generator 초안:
      SELECT c.name, SUM(oi.quantity * p.price) AS total FROM ...
  🔧 Critic → validate_sql()
  🧐 Critic 판정: ❌ FAIL: OperationalError: no such column: c.name — customers 테이블의 이름 컬럼은 cust_name입니다 …

  ── 반복 2 ──
  ✍️  Generator 초안:
      SELECT c.cust_name, SUM(oi.qty * p.unit_price_krw) AS total FROM customers c JOIN ...
      WHERE o.status NOT IN ('CANCELLED', 'REFUNDED') GROUP BY c.cust_id ORDER BY total DESC
  🔧 Critic → validate_sql()
  🧐 Critic 판정: ✅ PASS
  🏁 exit_condition 'PASS' 충족 → 루프 종료

  📊 최종 SQL 실행 결과 (6행)
     ['cust_name', 'total']
     ('한소희', 1138000)
     ('김민준', 1001000)
     ...
  🎯 정답 비교: 일치
```

`all`로 실행하면 마지막에 채점 요약이 나옵니다.

```
📋 채점 요약
  #1 [쉬움] 반복 1회, Critic PASS, 정답 일치
  ...
  #7 [어려움] 반복 3회, Critic PASS, 정답 불일치
  정답 7/8, 평균 반복 1.6회
```

> 위 SQL과 횟수는 예시입니다. 실제로는 모델에 따라 첫 시도에 바로 PASS가 나오기도 하고, 여러 번 반복하기도 합니다.

### 수업 포인트: "Critic PASS"와 "정답"은 다르다

채점 요약에서 **Critic은 PASS인데 정답은 불일치**인 경우가 나올 수 있습니다.
Critic은 "실행되는가"와 "질문에 맞아 보이는가"까지만 판단합니다. 그래서 질문 속의 미묘한 조건(예: "취소·환불 제외")을 놓친 SQL을 통과시킬 수 있습니다.
평가자의 기준이 곧 시스템의 품질 상한이라는 점, 그리고 평가 기준을 더 구체적으로 만들어야 하는 이유를 보여 주는 좋은 사례입니다. 아래 실습 과제 2번을 참고하세요.

### 웹 UI로 실행 (`adk web`)

```bash
mkdir -p sql_loop
cp adk_generator_critic.py sql_loop/agent.py
cp -r data sql_loop/data
echo "from . import agent" > sql_loop/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > sql_loop/.env      # 또는 ANTHROPIC_API_KEY=... / OPENAI_API_KEY=...
adk web                              # 브라우저에서 http://localhost:8000 → sql_loop 선택
```

> 웹 UI에서는 세션 상태에 `question`과 `schema`가 들어가지 않아 `Context variable not found` 오류가 납니다.
> State 탭에서 두 값을 먼저 넣거나, 명령행 실행(`python adk_generator_critic.py`)을 사용하세요.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 모델 공급자 | `export ADK_PROVIDER=gemini` / `claude` / `openai` | 설정된 키로 자동 감지 |
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` (또는 `claude-opus-5-5`, `gpt-5.6-luna` …) | 공급자별 기본 모델 |
| 공급자별 기본 모델 | 코드의 `DEFAULT_MODELS` | Gemini `gemini-3.8-flash` · Claude `claude-sonnet-5-5` · OpenAI `gpt-5.6` |
| 최대 반복 횟수 | `MAX_ITERATIONS=3 python ...` | 5 |
| DB 스키마·데이터 | `data/shop_schema.sql` 수정 | 테이블 4개 |
| 문제 추가 | `data/questions.json`에 `id`, `level`, `question`, `expected_sql` 추가 | 8문제 |
| 종료 조건 | `ExitConditionChecker`의 `condition_key`, `exit_condition` | `feedback` / `PASS` |

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
| `Context variable not found: feedback` | instruction에 `{feedback}`을 쓴 경우. 첫 바퀴용으로 `{feedback?}`처럼 `?`를 붙이기 |
| 루프가 끝나지 않고 매번 max_iterations까지 감 | Critic이 정확히 `PASS`로 시작하는 답을 내지 않음(예: "통과입니다"). Critic instruction의 출력 형식을 강조하거나, `exit_condition`을 확인 |
| 같은 오류가 반복됨 | Generator가 피드백을 무시하는 경우. 더 강한 모델을 쓰거나, Critic이 고칠 방법(올바른 컬럼 이름)을 구체적으로 쓰게 하기 |
| `429 Resource exhausted` | 반복마다 모델 호출이 3회씩 일어나 무료 등급 한도에 걸릴 수 있음. 잠시 후 다시 실행하거나 `MAX_ITERATIONS`를 줄이기 |

## 실습 과제 아이디어

1. **종료 조건 실험**: `ExitConditionChecker`를 빼고 실행하면 PASS가 나와도 `max_iterations`까지 계속 도는 것을 확인해 보세요. 반대로 Critic에게 ADK 내장 `exit_loop` 도구를 주어 LLM이 스스로 루프를 끝내게 바꾸고, 두 방식의 장단점을 비교해 보세요.
2. **더 엄격한 Critic**: Critic이 "Critic PASS·정답 불일치" 문제를 잡도록 바꿔 보세요. 예를 들어 질문의 조건(제외 조건, 정렬, 개수 제한)을 체크리스트로 하나씩 확인하게 하거나, 결과 행 수가 상식적인지 따져 보게 할 수 있습니다.
3. **반복 횟수 통계**: `all`을 여러 모델(`ADK_MODEL`)로 실행해 정답률과 평균 반복 횟수를 표로 비교해 보세요.
4. **Iterative Refinement로 확장**: PASS한 SQL을 한 번 더 받아 "인덱스를 고려한 더 효율적인 쿼리"로 다듬는 Refiner 루프를 뒤에 붙여 보세요.
