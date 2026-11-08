# ADK Parallel Fan-Out/Gather 예제 — 병렬 코드 리뷰

Google ADK(Agent Development Kit)로 구현한 **Parallel Fan-Out/Gather(문어 · 스웜) 패턴** 실습 예제입니다.
보안·스타일·성능 리뷰어 세 명이 **동시에** 같은 코드를 리뷰하고, 마지막에 요약 에이전트가 세 결과를 **하나의 PR 리뷰 코멘트로 종합**합니다.

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
                               ┌─▶ SecurityAuditor     ─(scan_security_patterns)─▶ state["security_report"]
 session.state                 │
 ["code"] ─▶ CodeReviewSwarm ──┼─▶ StyleEnforcer       ─(run_pep8_check)─────────▶ state["style_report"]
            (ParallelAgent)    │
            ※ 세 명이 동시에 실행 └─▶ PerformanceAnalyst  ─(analyze_complexity)─────▶ state["performance_report"]
                                                         │ 셋 다 끝나면
                                                         ▼
                        PRSummarizer  ◀── {security_report} {style_report} {performance_report}
                                      ─▶ state["pr_review"]  (최종 PR 리뷰 코멘트)

 workflow = SequentialAgent([CodeReviewSwarm, PRSummarizer])
```

| 에이전트 | 역할 | 근거 도구 | 결과 저장 위치 |
|---|---|---|---|
| `SecurityAuditor` | 인젝션 등 보안 취약점 | `scan_security_patterns` — SQL/명령 인젝션, eval, pickle, 하드코딩된 비밀, 약한 해시 등 패턴 검사 | `security_report` |
| `StyleEnforcer` | PEP8·형식·이름 규칙 | `run_pep8_check` — **pycodestyle** 실행 + 이름 규칙(AST) | `style_report` |
| `PerformanceAnalyst` | 시간 복잡도·자원 사용 | `analyze_complexity` — AST로 반복문 중첩 깊이, 문자열 누적, 리스트 멤버십, 반복 I/O, 다중 재귀 탐지 | `performance_report` |
| `PRSummarizer` | 세 보고서를 하나로 종합, 판정 | — | `pr_review` |

**핵심 포인트**

- **Fan-out (`ParallelAgent`)**: 서로 의존하지 않는 리뷰를 동시에 실행해 전체 대기 시간을 줄입니다. 순차 실행이면 세 리뷰 시간의 합만큼, 병렬 실행이면 가장 오래 걸리는 리뷰 하나만큼 걸립니다.
- **Gather (`SequentialAgent`로 감싸기)**: `ParallelAgent`는 결과를 합치지 않습니다. 그래서 `SequentialAgent`로 감싸 병렬 단계가 **모두 끝난 다음** `PRSummarizer`가 실행되도록 합니다.
- **고유한 `output_key`**: 병렬 에이전트들은 `session.state`를 함께 씁니다. 같은 키에 쓰면 나중에 끝난 쪽이 덮어쓰므로(경쟁 조건) 리뷰어마다 키를 다르게 둡니다.
- **도구로 근거 확보**: 블로그 원본에는 도구가 없지만, 이 예제는 리뷰어마다 정적 분석 도구를 붙였습니다. LLM이 줄 번호나 문제를 지어내지 않고 도구 결과를 근거로 리뷰하게 하기 위해서입니다.
- **공유 입력**: 리뷰할 코드는 세션을 만들 때 `session.state`에 넣어 둡니다. 리뷰어는 instruction의 `{code}`로 읽고, 도구는 `ToolContext`로 상태에서 직접 읽습니다.

## 폴더 구성

```
33_adk_parallel_pipeline/
├── adk_parallel_code_review.py      # 이 예제
├── README.md
├── data/
│   └── pr_samples/                  # 리뷰 실습용 PR 코드 (일부러 문제를 넣음)
│       ├── user_service.py          # 보안 문제 다수 + 성능 문제
│       ├── report_utils.py          # 스타일·성능 문제 위주
│       └── clean_stats.py           # 비교적 잘 작성된 코드 (대조군)
└── reviews/                         # 실행하면 생성: <파일명>_review.md
```

샘플 코드에 들어 있는 문제 (정적 분석 도구 기준):

| 파일 | 보안 | 스타일 (PEP8) | 성능 | 기대 판정 |
|---|---|---|---|---|
| `user_service.py` | HIGH 5건 (하드코딩된 키, SQL 인젝션, `shell=True`, `pickle.loads`, `eval`), MEDIUM 1건 (md5), LOW 1건 (/tmp) | 4건 (`import` 한 줄 다중, 연산자 공백) | 이중 반복문 O(n²), 문자열 `+=` 누적, 리스트 멤버십 검사 | ❌ Request changes |
| `report_utils.py` | 없음 | 9건 + 이름 규칙 3건 (`reportGenerator`, `TotalByMonth`, `Sales`) | 메모이제이션 없는 재귀 O(2ⁿ), 반복문 안의 파일 열기, 이중 반복문 | 💬 Comment 또는 ❌ |
| `clean_stats.py` | 없음 | 없음 | 없음 (set 멤버십은 O(1)이라 정상) | ✅ Approve |

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
cd 33_adk_parallel_pipeline

conda deactivate                   # 프롬프트 앞에 (base)가 보이면 먼저 빠져나오기 (Anaconda 사용자만)
python3 -m venv .venv              # 가상환경 만들기 (처음 한 번)
source .venv/bin/activate          # 가상환경 켜기   (Windows: .venv\Scripts\activate)
```

✅ **확인**: 프롬프트 맨 앞에 `(.venv)`가 붙고, 아래 명령의 경로가 이 폴더의 `.venv` 안을 가리키면 성공입니다.

```bash
which python                       # …/33_adk_parallel_pipeline/.venv/bin/python
```

> 💡 31~37번 예제를 모두 실습한다면, 폴더마다 만들지 않고 공용 환경 하나(`python3 -m venv ~/venvs/adk` → `source ~/venvs/adk/bin/activate`)를 만들어 함께 써도 됩니다.

### Step 2. 패키지 설치하기

```bash
pip install -U google-adk pycodestyle

# 사용할 모델에 따라 하나 더 설치 (Gemini만 쓰면 생략)
pip install -U anthropic           # Claude (Anthropic API 키)
pip install -U openai              # OpenAI GPT (OpenAI API 키)
```

| 패키지 | 용도 |
|---|---|
| `google-adk` | 에이전트 프레임워크 (2.11.0에서 확인) |
| `pycodestyle` | StyleEnforcer가 쓰는 PEP8 검사 도구 |
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
python adk_parallel_code_review.py
```

✅ **확인**: 실행하면 어떤 모델로 실행되는지 먼저 표시됩니다. 설정한 키에 맞는 모델이 나오면 정상입니다.

```
🧠 사용 모델: Gemini (gemini-3.8-flash)
```

다른 방법으로도 실행해 보세요.

```bash
# 1) 기본 실행: data/pr_samples/user_service.py 리뷰
python adk_parallel_code_review.py

# 2) 특정 파일 리뷰
python adk_parallel_code_review.py data/pr_samples/report_utils.py

# 3) 폴더 안의 .py 파일을 차례로 모두 리뷰
python adk_parallel_code_review.py data/pr_samples/

# 4) 내 코드 리뷰, 결과 파일은 저장하지 않기
python adk_parallel_code_review.py ~/projects/app/main.py --no-save
```

### Step 6. 결과 확인하기

**관찰 포인트**

- **실행 타임라인**에서 세 리뷰어의 막대가 같은 구간에 겹쳐 있으면 **동시에 실행**된 것입니다(Fan-out).
- `PRSummarizer`는 세 리뷰어가 **모두 끝난 뒤**에 시작합니다(Gather).
- `user_service.py`는 보안 HIGH 문제가 있어 `❌ Request changes`, `clean_stats.py`는 `✅ Approve`가 기대 판정입니다.
- 결과는 `reviews/<파일명>_review.md`에 저장됩니다. 세 리뷰어의 원본 보고서도 함께 들어 있습니다.

#### 출력 예시

도구 호출 시각과 **실행 타임라인**이 함께 표시됩니다. 세 리뷰어의 막대가 같은 구간에 겹쳐 있으면 동시에 실행된 것입니다.

```
======================================================================
▶ 리뷰 대상: data/pr_samples/user_service.py
======================================================================
     1.8s  [SecurityAuditor] 도구 호출 → scan_security_patterns
     1.9s  [PerformanceAnalyst] 도구 호출 → analyze_complexity
     2.0s  [StyleEnforcer] 도구 호출 → run_pep8_check
     6.4s  [StyleEnforcer] 완료
     8.1s  [PerformanceAnalyst] 완료
     9.0s  [SecurityAuditor] 완료
    14.2s  [PRSummarizer] 완료

  실행 타임라인 (첫 이벤트 → 마지막 이벤트, 초) — 막대가 겹치면 동시에 실행된 것
  SecurityAuditor        1.8 →   9.0  █████████████████████
  PerformanceAnalyst     1.9 →   8.1  ██████████████████
  StyleEnforcer          2.0 →   6.4  █████████████
  PRSummarizer          10.1 →  14.2                         ████████████

----- 🔒 SecurityAuditor (state['security_report']) -----
HIGH 5건, MEDIUM 1건, LOW 1건
- [HIGH] 12행 — SQL 인젝션 … → cur.execute("... WHERE name = ?", (username,))
...

######################################################################
📝 PRSummarizer — 최종 PR 리뷰 (state['pr_review'])
######################################################################
❌ Request changes — SQL 인젝션, shell=True 등 HIGH 보안 문제 5건
...
💾 저장: reviews/user_service_review.md
```

> 위 시간과 문장은 예시입니다. 실제 값은 모델과 네트워크 상황에 따라, 리뷰 문장은 실행할 때마다 달라집니다.
> 도구가 찾아내는 항목(줄 번호, 위반 개수)은 항상 같습니다.

결과는 `reviews/<파일명>_review.md`에 **최종 PR 리뷰 + 세 리뷰어의 원본 보고서**로 저장됩니다. GitHub PR 코멘트에 그대로 붙여 넣을 수 있는 마크다운입니다.

### 다음에 다시 실행할 때

Step 1~3은 다시 할 필요 없습니다. 새 터미널에서는 아래 네 줄이면 됩니다.

```bash
cd 33_adk_parallel_pipeline
source .venv/bin/activate                # (.venv) 확인
export GOOGLE_API_KEY="..."              # ~/.zshrc에 넣어 두었다면 생략
python adk_parallel_code_review.py
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
ADK_PROVIDER=claude python adk_parallel_code_review.py
ADK_PROVIDER=openai python adk_parallel_code_review.py

# 모델 이름까지 직접 지정 (이름으로 공급자를 판단: claude-* → Claude, gpt-*/o* → OpenAI, 그 외 → Gemini)
ADK_MODEL=claude-opus-5-5 python adk_parallel_code_review.py
ADK_MODEL=gpt-5.6-luna    python adk_parallel_code_review.py
ADK_MODEL=gemini-3.5-flash-lite python adk_parallel_code_review.py
```

**Vertex AI(Google Cloud)를 쓰는 경우**에는 API 키 대신 다음을 설정합니다.

```bash
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="내-프로젝트-ID"
export GOOGLE_CLOUD_LOCATION="us-central1"
gcloud auth application-default login
```

> **Claude를 Anthropic API 키로 쓸 때 주의**: ADK에 `model="claude-sonnet-5-5"`처럼 이름만 넘기면, ADK는 이것을 **Vertex AI(Google Cloud)의 Claude**로 연결해 Google Cloud 프로젝트를 요구합니다.
> 이 예제는 Anthropic API 키가 있으면 `AnthropicLlm(model=...)` 객체로 감싸서 Anthropic API로 직접 연결합니다(코드의 `resolve_model()` 참고).

## 웹 UI로 실행 (`adk web`)

```bash
mkdir -p code_review
cp adk_parallel_code_review.py code_review/agent.py
echo "from . import agent" > code_review/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > code_review/.env      # 또는 ANTHROPIC_API_KEY=... / OPENAI_API_KEY=...
adk web                              # 브라우저에서 http://localhost:8000 → code_review 선택
```

> 웹 UI에서는 세션을 만들 때 코드가 `session.state`에 들어가지 않으므로, instruction의 `{code}`에서 오류가 납니다.
> 웹 UI로 실습하려면 State 탭에서 `file_name`, `code`, `code_raw`를 먼저 넣거나, 명령행 실행(`python adk_parallel_code_review.py`)을 사용하세요.

> `adk web`은 에이전트 폴더의 `.env` 파일에서 키를 읽습니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 모델 공급자 | `export ADK_PROVIDER=gemini` / `claude` / `openai` | 설정된 키로 자동 감지 |
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` (또는 `claude-opus-5-5`, `gpt-5.6-luna` …) | 공급자별 기본 모델 |
| 공급자별 기본 모델 | 코드의 `DEFAULT_MODELS` | Gemini `gemini-3.8-flash` · Claude `claude-sonnet-5-5` · OpenAI `gpt-5.6` |
| 보안 검사 규칙 | 코드의 `SECURITY_RULES`에 (심각도, 이름, 정규식, 수정 방법) 추가 | 8개 규칙 |
| 한 줄 최대 길이 | `run_pep8_check`의 `max_line_length` | 79 |
| 리뷰어 추가 | `LlmAgent`를 하나 더 만들어 `parallel_reviews.sub_agents`에 추가하고, `PRSummarizer` instruction에 새 `{output_key}` 추가 | 3명 |
| 결과 파일 저장 | `--no-save` 옵션으로 끄기 | `reviews/`에 저장 |

## 실습 과제 아이디어

1. **순차 vs 병렬 비교**: `parallel_reviews`를 `SequentialAgent`로 바꿔 실행 타임라인과 총 소요 시간을 비교해 보세요.
2. **키 충돌 실험**: 두 리뷰어의 `output_key`를 같은 이름으로 바꾸면 `PRSummarizer`가 무엇을 받는지 확인해 보세요 (경쟁 조건).
3. **리뷰어 추가**: 테스트 누락을 점검하는 `TestCoverageReviewer`를 네 번째 병렬 워커로 추가해 보세요.
4. **Generator & Critic 결합**: `PRSummarizer` 뒤에 "리뷰가 너무 공격적이지 않은지" 점검하는 Critic 루프를 붙여 보세요.
5. **실제 PR에 적용**: `git diff`로 바뀐 파일만 골라 이 스크립트에 넘기는 셸 스크립트를 만들어 보세요.

## 문제 해결

**설치·환경 (Step 1~2)**

| 증상 | 원인과 해결 |
|---|---|
| `pip's dependency resolver ... incompatible` (예: `mlflow ... requires starlette<1`) | 기존 환경(Anaconda `base` 등)에 설치해서 다른 패키지와 충돌. `conda deactivate` 후 [Step 1](#step-1-가상환경-만들기)대로 **가상환경을 따로 만들어** 설치 |
| 프롬프트에 `(.venv)`가 없음 / `which python`이 `/opt/anaconda3/...` | 가상환경이 꺼져 있음. 이 폴더에서 `source .venv/bin/activate` |
| `ModuleNotFoundError: google.adk` / `pycodestyle` | 가상환경을 활성화했는지 확인하고 `pip install -U google-adk pycodestyle` |
| `Claude를 쓰려면 anthropic 패키지가 필요합니다` / `OpenAI 모델을 쓰려면 openai 패키지가 필요합니다` | `pip install -U anthropic` / `pip install -U openai` |

**API 키 (Step 3~4)**

| 증상 | 원인과 해결 |
|---|---|
| `API 키가 설정되어 있지 않습니다` | `echo $GOOGLE_API_KEY $ANTHROPIC_API_KEY $OPENAI_API_KEY`로 현재 터미널에 키가 있는지 확인. 새 터미널을 열었다면 `export`를 다시 하거나 `~/.zshrc`에 등록 |
| `❌ API 키 인증 실패` (`Unauthorized`, `401`) | 키 값 오타, 만료된 키, 또는 **구독 로그인 정보를 키로 착각**한 경우. [Step 3](#step-3-api-키-발급받기)의 페이지에서 API 키를 새로 발급 |
| `GOOGLE_CLOUD_PROJECT ... must be set` (Claude 사용 시) | Claude가 Vertex AI로 연결된 경우. `ANTHROPIC_API_KEY`를 설정하고 `GOOGLE_GENAI_USE_VERTEXAI`는 해제 |
| 의도와 다른 공급자가 선택됨 | 키가 여러 개 설정됨. `ADK_PROVIDER=claude`처럼 직접 지정 ([모델 고르기](#모델-고르기-키가-여러-개일-때)) |

**실행 중 (Step 5~6)**

| 증상 | 원인과 해결 |
|---|---|
| `404 ... model not found` / `model_not_found` | 계정에서 쓸 수 없는 모델 이름. 각 공급자의 모델 목록에서 확인해 `ADK_MODEL`로 지정 |
| `503 UNAVAILABLE` / `high demand` / `⏳ 모델 서버가 일시적으로 응답하지 못했습니다` | 코드 문제가 아니라 모델 서버의 일시적 과부하. Gemini는 자동으로 최대 6번(약 1분) 재시도하며, 그래도 실패하면 이 안내가 나옴. 1~2분 뒤 다시 실행하거나 `ADK_MODEL=gemini-3.5-flash-lite`처럼 가벼운 모델, 또는 `ADK_PROVIDER=claude`/`openai`로 다른 공급자 사용 |
| `Context variable not found` 오류 (`code` 변수) | `{code}`, `{file_name}`이 세션 상태에 없음. `adk web` 대신 `python adk_parallel_code_review.py`로 실행 |
| `429 Resource exhausted` | 세 리뷰어가 동시에 요청하므로 무료 등급 분당 한도에 걸릴 수 있음. 잠시 후 다시 실행하거나 더 가벼운 모델 사용 |
| 타임라인 막대가 겹치지 않음 | 모델 응답이 매우 빠르거나 API가 요청을 순서대로 처리한 경우. 큰 파일로 시험하면 차이가 더 잘 보임 |
| 구문 오류가 있는 파일 | 스타일·성능 도구가 `구문 오류로 분석할 수 없습니다`를 반환하고, 리뷰어는 코드만 보고 리뷰함 |
