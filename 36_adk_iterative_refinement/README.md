# ADK Iterative Refinement 예제 — 알고리즘 성능 최적화 루프

Google ADK(Agent Development Kit)로 구현한 **Iterative Refinement(조각가) 패턴** 실습 예제입니다.
Generator가 거친 첫 초안을 쓰면, Critic이 **실제로 실행·측정**해 개선점을 제안합니다. 그러면 Refiner가 더 빠른 버전으로 다시 씁니다. 이 과정을 정해진 횟수만큼 반복하며 코드를 점점 다듬습니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다. 블로그 그림의 예시("Optimize complex algorithm for performance")를 따랐습니다.

**Gemini · Claude · OpenAI 모두 지원합니다.** Google API 키, Claude Code에서 쓰는 Anthropic API 키, Codex에서 쓰는 OpenAI API 키 중 하나만 있으면 코드를 고치지 않고 실행됩니다(키를 자동으로 감지).

**바로 실습하려면 → [따라 하기: 설치부터 실행까지](#따라-하기-설치부터-실행까지)**

## 목차

1. [구조](#구조)
2. [블로그 의사코드와 다른 점](#블로그-의사코드와-다른-점)
3. [폴더 구성](#폴더-구성)
4. [**따라 하기: 설치부터 실행까지**](#따라-하기-설치부터-실행까지) ← Step 1 ~ Step 6
5. [모델 고르기 (키가 여러 개일 때)](#모델-고르기-키가-여러-개일-때)
6. [웹 UI로 실행 (`adk web`)](#웹-ui로-실행-adk-web)
7. [안전에 관한 주의](#안전에-관한-주의)
8. [설정 바꾸기](#설정-바꾸기)
9. [실습 과제 아이디어](#실습-과제-아이디어)
10. [문제 해결](#문제-해결)

## 구조

```
workflow = SequentialAgent([Generator, RefinementLoop])

① Generator ─ 문제를 그대로 옮긴 직관적인 첫 버전(v1) ─────────────▶ state["current_draft"]

② RefinementLoop (LoopAgent, max_iterations=3)
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ Critic       benchmark_current_draft 도구로 정확성·실행 시간 측정           │
   │              + 복잡도 분석과 개선 방법 제안        ──▶ state["critique_notes"] │
   │ QualityGate  정답이고 목표 시간 이내면 escalate → 루프 조기 종료 (추가 단계)   │
   │ Refiner      {current_draft} + {critique_notes} → 더 빠른 버전              │
   │                                                  ──▶ state["current_draft"] │
   │                                                     (같은 키에 덮어쓰기)     │
   └──────────────────────────── 반복 ────────────────────────────────────────────┘
```

| 단계 | 에이전트 | 하는 일 | 상태 키 |
|---|---|---|---|
| ① | `Generator` | 성능은 신경 쓰지 않은 직관적인 첫 초안 | `current_draft` |
| ② | `Critic` | 초안을 실제로 실행해 정답 여부·실행 시간 측정 → 시간 복잡도 분석 → 개선 방법 2~4개 제안 | `critique_notes` |
| ② | `QualityGate` (일반 코드) | 목표 시간 달성 시 `escalate`로 루프 종료 | — |
| ② | `Refiner` | 제안을 반영해 함수 전체를 다시 작성 | `current_draft` (덮어쓰기) |

**핵심 포인트**

- **덮어쓰기(`output_key="current_draft"`)**: Generator와 Refiner가 같은 키에 씁니다. 그래서 다음 바퀴의 Critic은 항상 최신 버전을 봅니다. 조각가가 같은 돌을 계속 깎아 나가는 것과 같습니다.
- **`max_iterations`는 하드 리밋**: 품질이 더 오르지 않아도 정해진 횟수가 지나면 멈추는 안전장치입니다.
- **조기 종료(`escalate`)**: 블로그는 에이전트가 `EventActions(escalate=True)`로 일찍 끝낼 수 있다고 설명합니다. 이 예제에서는 측정값이 목표를 만족하면 `QualityGate`가 escalate합니다.
- **Generator & Critic과의 차이**: 그 패턴은 **맞다/틀리다**를 판정해 통과하면 끝납니다. 이 패턴은 이미 맞는 코드도 **더 좋게** 만드는 것이 목적이라, 기본적으로 정해진 횟수만큼 다듬습니다.

## 블로그 의사코드와 다른 점

| 의사코드 | 이 예제 | 이유 |
|---|---|---|
| `sub_agents=[critic, refiner]` | `sub_agents=[critic, QualityGate, refiner]` | 블로그가 언급한 escalate 조기 종료를 구현. `ENABLE_QUALITY_GATE=0`으로 끄면 의사코드와 똑같이 3바퀴를 모두 돕니다. |
| Critic이 눈으로 검토 | Critic에 `benchmark_current_draft` 도구 | "더 빨라졌다"를 말이 아니라 **측정값**으로 판단하기 위해서입니다. |
| — | 버전별 측정 기록(`state["history"]`)과 개선 추이 표 | 반복마다 얼마나 좋아졌는지 눈으로 확인하기 위해서입니다. |

나머지(에이전트 이름, `output_key`, `max_iterations=3`, `SequentialAgent([generator, loop])`)는 의사코드 그대로입니다.

> 참고: ADK 2.x에서 `LoopAgent`는 **deprecated**로 표시되어 있습니다(그래프 기반 `Workflow`로 대체 예정). 아직 정상 동작하며, 경고 메시지는 코드에서 숨겼습니다.

## 폴더 구성

```
36_adk_iterative_refinement/
├── adk_iterative_refinement.py   # 이 예제
├── README.md
├── data/
│   └── tasks.json                # 최적화 과제 3개 (설명, 정확성 테스트, 성능 측정 입력, 목표 시간)
└── results/                      # 실행하면 생성: <함수명>_optimized.py (최종 버전)
```

### 과제 (`data/tasks.json`)

직관적인 풀이와 효율적인 풀이의 차이가 수백~수천 배 나도록 골랐습니다.

| # | 함수 | 문제 | 직관적인 풀이 | 목표 (큰 입력) | 개선 방향 |
|---|---|---|---|---|---|
| 1 | `count_pairs` | 합이 k인 쌍의 개수 (n=6,000) | 이중 반복문 O(n²) — 약 0.8초 | 20ms | 해시맵 한 번 순회 O(n) |
| 2 | `primes_up_to` | n 이하의 소수 (n=60,000) | 모든 수로 나눠 보기 — 약 6초 | 40ms | √n까지만 나누기(약 50ms, 아직 미달) → **에라토스테네스의 체** |
| 3 | `climb_ways` | 계단 오르는 방법의 수 (n=5,000) | 단순 재귀 — 지수 시간, 끝나지 않음 | 40ms | 메모이제이션 / 동적 계획법 O(n·k) |

> 시간은 실습 환경 기준 대략값입니다. 2번은 한 번의 개선(√n)으로는 목표에 못 미쳐, **여러 바퀴에 걸쳐 점점 나아지는 과정**을 관찰하기 좋습니다.

각 과제에는 정확성 테스트 5개와 정답값이 들어 있습니다. 정답값은 별도의 정답 풀이로 미리 계산해 두었습니다. 빠르지만 틀린 코드는 실패로 처리합니다.

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
cd 36_adk_iterative_refinement

conda deactivate                   # 프롬프트 앞에 (base)가 보이면 먼저 빠져나오기 (Anaconda 사용자만)
python3 -m venv .venv              # 가상환경 만들기 (처음 한 번)
source .venv/bin/activate          # 가상환경 켜기   (Windows: .venv\Scripts\activate)
```

✅ **확인**: 프롬프트 맨 앞에 `(.venv)`가 붙고, 아래 명령의 경로가 이 폴더의 `.venv` 안을 가리키면 성공입니다.

```bash
which python                       # …/36_adk_iterative_refinement/.venv/bin/python
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
python adk_iterative_refinement.py 2
```

✅ **확인**: 실행하면 어떤 모델로 실행되는지 먼저 표시됩니다. 설정한 키에 맞는 모델이 나오면 정상입니다.

```
🧠 사용 모델: Gemini (gemini-3.8-flash)
```

다른 방법으로도 실행해 보세요.

```bash
# 1) 과제 목록 보기
python adk_iterative_refinement.py

# 2) 특정 과제 최적화
python adk_iterative_refinement.py 2

# 3) 세 과제 모두
python adk_iterative_refinement.py all

# 4) 블로그 의사코드와 똑같이: 조기 종료 없이 3바퀴 고정
ENABLE_QUALITY_GATE=0 python adk_iterative_refinement.py 2

# 5) 반복 횟수 늘리기
MAX_ITERATIONS=5 python adk_iterative_refinement.py 3
```

### Step 6. 결과 확인하기

**관찰 포인트**

- `📏 Critic 측정 vN`의 실행 시간이 바퀴마다 **얼마나 줄어드는지** 보세요(예: 수천 ms → 수십 ms → 1~2 ms).
- 목표 시간을 달성하면 `🏁 QualityGate: 목표 달성 → escalate로 루프 조기 종료`가 나오고 남은 바퀴를 건너뜁니다.
- 마지막의 **버전별 개선 추이 표**에서 v1부터 최종 버전까지의 변화를 한눈에 확인할 수 있습니다.
- 최종 코드는 `results/<함수명>_optimized.py`에 저장됩니다. 마지막 수정이 오히려 나빠지면 ⚠️ 경고가 나옵니다.

#### 출력 예시

```
======================================================================
▶ 과제 #2: primes_up_to (max_iterations=3, QualityGate 켜짐)
======================================================================

  ✍️  Generator: 첫 초안(v1) 작성 — 2줄

  ── 반복 1 ──
  📏 Critic 측정 v1: ✅ 정답, 5715.2ms   (목표 40ms)
  🧐 Critic 제안: 1. 모든 수로 나누는 대신 √x까지만 … / 2. 에라토스테네스의 체로 …
  🛠️  Refiner: v2 작성 (current_draft 덮어쓰기)

  ── 반복 2 ──
  📏 Critic 측정 v2: ✅ 정답, 54.2ms   (목표 40ms)
  🧐 Critic 제안: 1. 여전히 O(n√n) — 체로 바꾸면 O(n log log n) …
  🛠️  Refiner: v3 작성 (current_draft 덮어쓰기)

  ── 반복 3 ──
  📏 Critic 측정 v3: ✅ 정답, 1.4ms 🎯(목표 40ms)
  🧐 Critic 제안: …
  🏁 QualityGate: 목표 달성 → escalate로 루프 조기 종료

  📈 버전별 개선 추이 (primes_up_to)
     버전    결과
     v1    ✅ 정답, 5715.2ms   (목표 40ms)
     v2    ✅ 정답, 54.2ms   (목표 40ms)
     v3    ✅ 정답, 1.4ms 🎯(목표 40ms)
     → 첫 정답 버전 대비 3921.7배 빨라짐
  💾 최종 코드 저장: results/primes_up_to_optimized.py
```

> 위 과정은 예시입니다. 실제 모델은 첫 초안부터 빠른 코드를 쓰기도 합니다(이때는 반복 1에서 바로 목표를 달성해 끝남). 한 번에 체까지 가기도 하고, 드물게 개선하다가 정답을 깨뜨리기도 합니다.
> 실행 시간은 컴퓨터 성능에 따라 달라집니다.

#### 최종 버전이 더 나빠지면

Refiner는 `current_draft`를 **덮어쓰기** 때문에, 마지막 수정이 오히려 정답을 깨거나 느려지면 이전의 좋은 버전이 사라집니다. 이런 경우 실행 결과에 경고가 나옵니다.

```
  ⚠️  최종 버전(v4)이 가장 좋았던 v3보다 나쁩니다 — 덮어쓰기 구조의 한계 (README 실습 과제 3 참고)
```

### 다음에 다시 실행할 때

Step 1~3은 다시 할 필요 없습니다. 새 터미널에서는 아래 네 줄이면 됩니다.

```bash
cd 36_adk_iterative_refinement
source .venv/bin/activate                # (.venv) 확인
export GOOGLE_API_KEY="..."              # ~/.zshrc에 넣어 두었다면 생략
python adk_iterative_refinement.py 2
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
ADK_PROVIDER=claude python adk_iterative_refinement.py 2
ADK_PROVIDER=openai python adk_iterative_refinement.py 2

# 모델 이름까지 직접 지정 (이름으로 공급자를 판단: claude-* → Claude, gpt-*/o* → OpenAI, 그 외 → Gemini)
ADK_MODEL=claude-opus-5-5 python adk_iterative_refinement.py 2
ADK_MODEL=gpt-5.6-luna    python adk_iterative_refinement.py 2
ADK_MODEL=gemini-3.5-flash-lite python adk_iterative_refinement.py 2
```

> **Claude를 Anthropic API 키로 쓸 때 주의**: ADK에 `model="claude-sonnet-5-5"`처럼 이름만 넘기면, ADK는 이것을 **Vertex AI(Google Cloud)의 Claude**로 연결해 Google Cloud 프로젝트를 요구합니다.
> 이 예제는 Anthropic API 키가 있으면 `AnthropicLlm(model=...)` 객체로 감싸서 Anthropic API로 직접 연결합니다(코드의 `resolve_model()` 참고).

## 웹 UI로 실행 (`adk web`)

```bash
mkdir -p refine_agent
cp adk_iterative_refinement.py refine_agent/agent.py
cp -r data refine_agent/data
echo "from . import agent" > refine_agent/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > refine_agent/.env      # 또는 ANTHROPIC_API_KEY=... / OPENAI_API_KEY=...
adk web                              # 브라우저에서 http://localhost:8000 → refine_agent 선택
```

> 웹 UI에서는 세션 상태에 `task`, `task_json`이 들어가지 않아 `Context variable not found` 오류가 납니다.
> 명령행 실행(`python adk_iterative_refinement.py`)을 권장합니다.

> `adk web`은 에이전트 폴더의 `.env` 파일에서 키를 읽습니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 안전에 관한 주의

이 예제는 **LLM이 작성한 코드를 실제로 실행**합니다. 벤치마크는 다음 조건으로 실행됩니다.

- 별도 프로세스에서 실행합니다(`python -I`: 사용자 환경 변수와 site-packages 영향 차단).
- 임시 폴더에서 실행합니다.
- `BENCH_TIMEOUT`(기본 10초)이 지나면 강제로 종료합니다.

이것은 실습용 안전장치일 뿐 **완전한 샌드박스가 아닙니다**. 과제 파일(`tasks.json`)은 신뢰할 수 있는 것만 사용하고, 중요한 파일이 있는 환경에서는 컨테이너나 가상 머신 안에서 실행하세요.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 모델 공급자 | `export ADK_PROVIDER=gemini` / `claude` / `openai` | 설정된 키로 자동 감지 |
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` (또는 `claude-opus-5-5`, `gpt-5.6-luna` …) | 공급자별 기본 모델 |
| 공급자별 기본 모델 | 코드의 `DEFAULT_MODELS` | Gemini `gemini-3.8-flash` · Claude `claude-sonnet-5-5` · OpenAI `gpt-5.6` |
| 최대 반복 횟수 | `MAX_ITERATIONS=5 python ...` | 3 |
| 조기 종료 | `ENABLE_QUALITY_GATE=0` 으로 끄기 | 켜짐 |
| 벤치마크 시간 제한 | `BENCH_TIMEOUT=20 python ...` (초) | 10 |
| 과제 추가 | `data/tasks.json`에 `func`, `signature`, `description`, `tests`, `perf_setup`, `perf_expected`, `target_ms` 추가 | 3개 |

## 실습 과제 아이디어

1. **조기 종료 효과 비교**: `ENABLE_QUALITY_GATE=1`과 `0`으로 같은 과제를 실행해 모델 호출 수(반복 횟수)와 최종 결과를 비교해 보세요.
2. **Critic 없이 다듬기**: Critic에서 벤치마크 도구를 빼고 "눈으로만" 검토하게 하면 개선 방향이 얼마나 정확한지 비교해 보세요. 측정 근거의 중요성을 확인할 수 있습니다.
3. **최고 버전 보존**: 덮어쓰기로 좋은 버전을 잃는 문제를 해결해 보세요. 예를 들어 벤치마크 도구가 측정할 때마다 가장 빠른 정답 코드를 `state["best_draft"]`에 따로 저장하고, 마지막에 그것을 결과로 쓰게 바꿀 수 있습니다.
4. **다른 품질 기준**: 실행 시간 대신 메모리 사용량(`tracemalloc`)이나 코드 가독성을 기준으로 다듬도록 Critic과 QualityGate를 바꿔 보세요.

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
| 반복 1에서 바로 끝남 | 모델이 첫 초안부터 효율적인 코드를 씀. 정상입니다. 개선 과정을 보고 싶으면 `ENABLE_QUALITY_GATE=0`으로 실행 |
| 측정마다 `시간 초과` | 아직 지수/이차 시간 풀이. Critic 제안대로 개선되는지 지켜보거나 `MAX_ITERATIONS`를 늘리기 |
| 한 번 실행에 오래 걸림 | 느린 초안은 측정에 최대 `BENCH_TIMEOUT`초가 걸림. 반복마다 모델 호출도 3회 이상 일어남 |
| `429 Resource exhausted` | 무료 등급 분당 한도. 잠시 후 다시 실행하거나 `MAX_ITERATIONS`를 줄이기 |
