# ADK Iterative Refinement 예제 — 알고리즘 성능 최적화 루프

Google ADK(Agent Development Kit)로 구현한 **Iterative Refinement(조각가) 패턴** 실습 예제입니다.
Generator가 거친 첫 초안을 쓰면, Critic이 **실제로 실행·측정**해 개선점을 제안합니다. 그러면 Refiner가 더 빠른 버전으로 다시 씁니다. 이 과정을 정해진 횟수만큼 반복하며 코드를 점점 다듬습니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다. 블로그 그림의 예시("Optimize complex algorithm for performance")를 따랐습니다.

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

## 설치

Python 3.10 이상이 필요합니다.

```bash
cd 36_adk_iterative_refinement
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

> `python`으로 직접 실행할 때는 위처럼 터미널에서 export해야 합니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 실행

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

### 출력 예시

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

### 웹 UI로 실행 (`adk web`)

```bash
mkdir -p refine_agent
cp adk_iterative_refinement.py refine_agent/agent.py
cp -r data refine_agent/data
echo "from . import agent" > refine_agent/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > refine_agent/.env
adk web                              # 브라우저에서 http://localhost:8000 → refine_agent 선택
```

> 웹 UI에서는 세션 상태에 `task`, `task_json`이 들어가지 않아 `Context variable not found` 오류가 납니다.
> 명령행 실행(`python adk_iterative_refinement.py`)을 권장합니다.

## 안전에 관한 주의

이 예제는 **LLM이 작성한 코드를 실제로 실행**합니다. 벤치마크는 다음 조건으로 실행됩니다.

- 별도 프로세스에서 실행합니다(`python -I`: 사용자 환경 변수와 site-packages 영향 차단).
- 임시 폴더에서 실행합니다.
- `BENCH_TIMEOUT`(기본 10초)이 지나면 강제로 종료합니다.

이것은 실습용 안전장치일 뿐 **완전한 샌드박스가 아닙니다**. 과제 파일(`tasks.json`)은 신뢰할 수 있는 것만 사용하고, 중요한 파일이 있는 환경에서는 컨테이너나 가상 머신 안에서 실행하세요.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` | `gemini-3.8-flash` |
| 최대 반복 횟수 | `MAX_ITERATIONS=5 python ...` | 3 |
| 조기 종료 | `ENABLE_QUALITY_GATE=0` 으로 끄기 | 켜짐 |
| 벤치마크 시간 제한 | `BENCH_TIMEOUT=20 python ...` (초) | 10 |
| 과제 추가 | `data/tasks.json`에 `func`, `signature`, `description`, `tests`, `perf_setup`, `perf_expected`, `target_ms` 추가 | 3개 |

## 문제 해결

| 증상 | 원인과 해결 |
|---|---|
| `ModuleNotFoundError: google.adk` | 가상환경을 활성화했는지 확인하고 `pip install -U google-adk` |
| API 키·인증 관련 오류 | `echo $GOOGLE_API_KEY`로 현재 터미널에 키가 설정되어 있는지 확인 |
| `404 ... model not found` | 사용 가능한 모델 ID로 `ADK_MODEL` 변경 (Google AI Studio의 모델 목록 참고) |
| 반복 1에서 바로 끝남 | 모델이 첫 초안부터 효율적인 코드를 씀. 정상입니다. 개선 과정을 보고 싶으면 `ENABLE_QUALITY_GATE=0`으로 실행 |
| 측정마다 `시간 초과` | 아직 지수/이차 시간 풀이. Critic 제안대로 개선되는지 지켜보거나 `MAX_ITERATIONS`를 늘리기 |
| 한 번 실행에 오래 걸림 | 느린 초안은 측정에 최대 `BENCH_TIMEOUT`초가 걸림. 반복마다 모델 호출도 3회 이상 일어남 |
| `429 Resource exhausted` | 무료 등급 분당 한도. 잠시 후 다시 실행하거나 `MAX_ITERATIONS`를 줄이기 |

## 실습 과제 아이디어

1. **조기 종료 효과 비교**: `ENABLE_QUALITY_GATE=1`과 `0`으로 같은 과제를 실행해 모델 호출 수(반복 횟수)와 최종 결과를 비교해 보세요.
2. **Critic 없이 다듬기**: Critic에서 벤치마크 도구를 빼고 "눈으로만" 검토하게 하면 개선 방향이 얼마나 정확한지 비교해 보세요. 측정 근거의 중요성을 확인할 수 있습니다.
3. **최고 버전 보존**: 덮어쓰기로 좋은 버전을 잃는 문제를 해결해 보세요. 예를 들어 벤치마크 도구가 측정할 때마다 가장 빠른 정답 코드를 `state["best_draft"]`에 따로 저장하고, 마지막에 그것을 결과로 쓰게 바꿀 수 있습니다.
4. **다른 품질 기준**: 실행 시간 대신 메모리 사용량(`tracemalloc`)이나 코드 가독성을 기준으로 다듬도록 Critic과 QualityGate를 바꿔 보세요.
