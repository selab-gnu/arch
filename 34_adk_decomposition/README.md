# ADK Hierarchical Decomposition 예제 — AI 트렌드 보고서 작성

Google ADK(Agent Development Kit)로 구현한 **Hierarchical Decomposition(러시아 인형) 패턴** 실습 예제입니다.
최상위 에이전트가 큰 작업(보고서 작성)을 하위 작업(조사)으로 쪼개 아래 계층에 맡기고, **결과를 돌려받아 자기 추론을 이어 갑니다.**

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다. (Level 2 연결 방식은 아래 설명처럼 바꿨습니다.)

**Gemini · Claude · OpenAI 모두 지원합니다.** Google API 키, Claude Code에서 쓰는 Anthropic API 키, Codex에서 쓰는 OpenAI API 키 중 하나만 있으면 코드를 고치지 않고 실행됩니다(키를 자동으로 감지).

**바로 실습하려면 → [따라 하기: 설치부터 실행까지](#따라-하기-설치부터-실행까지)**

## 목차

1. [구조](#구조)
2. [왜 Level 2도 AgentTool인가 (블로그 의사코드와 다른 점)](#왜-level-2도-agenttool인가-블로그-의사코드와-다른-점)
3. [폴더 구성](#폴더-구성)
4. [**따라 하기: 설치부터 실행까지**](#따라-하기-설치부터-실행까지) ← Step 1 ~ Step 6
5. [모델 고르기 (키가 여러 개일 때)](#모델-고르기-키가-여러-개일-때)
6. [웹 UI로 실행 (`adk web`)](#웹-ui로-실행-adk-web)
7. [설정 바꾸기](#설정-바꾸기)
8. [실습 과제 아이디어](#실습-과제-아이디어)
9. [문제 해결](#문제-해결)

## 구조

```
Level 1   ReportWriter  ─ 주제를 하위 주제 3~4개로 나누고, 조사 결과로 보고서 작성
             │  tools: AgentTool(ResearchAssistant)          ← 하위 계층 전체가 '함수 하나'
             ▼
Level 2   ResearchAssistant  ─ 조사 요청 하나 → 검색 → 요약 → 결과 반환
             │  tools: AgentTool(WebSearchAgent), AgentTool(SummarizerAgent)
             ▼
Level 3   WebSearchAgent  ─ 검색으로 출처가 달린 사실 수집   (search_web 또는 google_search)
          SummarizerAgent ─ 원문을 핵심 사실 몇 줄로 압축
```

한 번의 실행에서 일어나는 일 (하위 주제가 3개일 때):

```
ReportWriter ─▶ ResearchAssistant("AI 에이전트 기업 도입")
                   ├─▶ WebSearchAgent ─▶ search_web(...)  ─▶ 원문 반환
                   └─▶ SummarizerAgent(원문)              ─▶ 요약 반환
               ◀── 조사 결과 1
ReportWriter ─▶ ResearchAssistant("AI 규제 거버넌스")      … 같은 과정 반복
ReportWriter ─▶ ResearchAssistant("에이전트 보안")         … 같은 과정 반복
ReportWriter ─▶ 세 조사 결과를 바탕으로 보고서 작성
```

**핵심 포인트**

- **`AgentTool`**: 에이전트(와 그 아래 계층 전체)를 도구처럼 감쌉니다. 부모는 함수를 부르듯 호출하고, 결과가 돌아올 때까지 기다렸다가 이어서 추론합니다.
- **컨텍스트 분리**: 검색 원문처럼 긴 텍스트는 아래 계층에서만 오가고, 위로는 요약된 결과만 올라갑니다. 그래서 ReportWriter의 컨텍스트 창이 넘치지 않습니다. 이것이 "한 에이전트의 컨텍스트에 담기 힘든 큰 작업"에 이 패턴을 쓰는 이유입니다.
- **라우팅과의 차이**: Coordinator/Dispatcher는 제어권을 **넘기고 끝**입니다. Hierarchical Decomposition은 일을 **맡기고 결과를 회수**합니다.

## 왜 Level 2도 AgentTool인가 (블로그 의사코드와 다른 점)

블로그 의사코드에서는 ResearchAssistant가 `sub_agents=[web_searcher, summarizer]`로 하위 에이전트를 둡니다.
그런데 `sub_agents`는 ADK에서 **대화 제어권을 넘기는(transfer)** 방식입니다. 그래서 ResearchAssistant가 WebSearchAgent에게 넘기는 순간 ResearchAssistant의 차례가 끝나 버립니다.

ADK 2.11에서 같은 시나리오로 두 방식을 실행해 본 결과:

| Level 2 연결 방식 | 실제 실행 순서 | ReportWriter가 받은 것 |
|---|---|---|
| `sub_agents=[...]` (의사코드 그대로) | Writer → RA → **Search** → Writer | 검색 원문 그대로. **Summarizer는 실행되지 않음** |
| `tools=[AgentTool(...), AgentTool(...)]` (이 예제) | Writer → RA → Search → RA → **Summarizer** → RA → Writer | 검색 → 요약을 거친 조사 결과 |

블로그 그림도 Level 3를 "Tool Agents"로, ResearchAssistant의 도구를 `[WebSearch, Summarizer]`로 그리고 있습니다. 그 의도대로 동작하게 하려고 Level 2에서도 `AgentTool`을 썼습니다.
(직접 확인해 보려면 아래 [실습 과제](#실습-과제-아이디어) 1번을 해 보세요.)

## 폴더 구성

```
34_adk_decomposition/
├── adk_hierarchical_report.py   # 이 예제
├── README.md
├── data/
│   └── web_corpus.json          # 오프라인 검색용 '가상 웹' 문서 12건
└── reports/                     # 실행하면 생성: report_<날짜_시각>.md
```

### 가상 웹 코퍼스 (`data/web_corpus.json`)

수업 중 인터넷 연결이나 검색 결과 변화에 영향을 받지 않도록, 기본 모드에서는 이 파일을 검색 엔진처럼 씁니다.
**매체·조사기관·수치는 모두 실습용으로 만든 가상의 내용이며 실제 사실이 아닙니다.** (출처 이름에 모두 "(가상)"을 붙였습니다.)

| 주제 | 문서 | 주제 | 문서 |
|---|---|---|---|
| 기업의 에이전트 도입 | doc-01 | 데이터센터 전력 수요 | doc-05 |
| 멀티 에이전트 운영 | doc-02 | AI 코딩 도구 | doc-06 |
| 온디바이스 소형 모델 | doc-03 | 멀티모달 AI | doc-07 |
| AI 규제·거버넌스 | doc-04 | 환각 감소·평가 | doc-08 |
| 기업 AI 투자 | doc-09 | 오픈 웨이트 모델 | doc-10 |
| AI와 일자리 | doc-11 | 에이전트 보안 위협 | doc-12 |

문서를 추가하려면 같은 형식(`id`, `url`, `title`, `source`, `date`, `tags`, `body`)으로 `documents` 배열에 넣으면 됩니다. `tags`에 한국어·영어 키워드를 함께 넣으면 검색이 잘 됩니다.

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
cd 34_adk_decomposition

conda deactivate                   # 프롬프트 앞에 (base)가 보이면 먼저 빠져나오기 (Anaconda 사용자만)
python3 -m venv .venv              # 가상환경 만들기 (처음 한 번)
source .venv/bin/activate          # 가상환경 켜기   (Windows: .venv\Scripts\activate)
```

✅ **확인**: 프롬프트 맨 앞에 `(.venv)`가 붙고, 아래 명령의 경로가 이 폴더의 `.venv` 안을 가리키면 성공입니다.

```bash
which python                       # …/34_adk_decomposition/.venv/bin/python
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
python adk_hierarchical_report.py
```

✅ **확인**: 실행하면 어떤 모델로 실행되는지 먼저 표시됩니다. 설정한 키에 맞는 모델이 나오면 정상입니다.

```
🧠 사용 모델: Gemini (gemini-3.8-flash)
```

다른 방법으로도 실행해 보세요.

```bash
# 1) 기본: "2026년 AI 트렌드" 보고서 (가상 웹 검색)
python adk_hierarchical_report.py

# 2) 주제 지정
python adk_hierarchical_report.py "AI 에이전트 보안 위협과 대응"
python adk_hierarchical_report.py "온디바이스 AI와 에너지 효율"

# 3) 실제 웹 검색 (Gemini 내장 google_search)
python adk_hierarchical_report.py "2026년 AI 트렌드" --live

# 4) 결과 파일 저장하지 않기
python adk_hierarchical_report.py --no-save
```

### Step 6. 결과 확인하기

**관찰 포인트**

- 들여쓰기 트리에서 `[L1] → [L2] → [L3]`로 **아래 계층에 일을 맡기고, `완료 → 결과를 호출한 쪽으로 반환`으로 결과가 위로 돌아오는** 흐름을 볼 수 있습니다.
- 하위 주제마다 `ResearchAssistant`가 한 번씩 호출되고, 그 안에서 항상 `WebSearchAgent → SummarizerAgent` 순서로 실행됩니다.
- 검색 원문은 L3·L2 안에서만 오가고, ReportWriter(L1)에는 요약된 결과만 올라갑니다(컨텍스트 분리).
- 완성된 보고서는 `reports/report_<날짜_시각>.md`에 저장됩니다.

#### 출력 예시

실행 중에는 **어느 레벨의 어떤 에이전트가 무엇을 호출했는지** 들여쓰기 트리로 보여 줍니다.

```
▶ 주제: 2026년 AI 트렌드
▶ 검색 모드: 가상 웹 (data/web_corpus.json)

   1.2s  [L1 ReportWriter] 시작
   3.4s  [L1 ReportWriter] 🔧 ResearchAssistant('AI 에이전트의 기업 도입 현황')
   3.4s      [L2 ResearchAssistant] 시작
   4.9s      [L2 ResearchAssistant] 🔧 WebSearchAgent('AI 에이전트 기업 도입 현황')
   4.9s          [L3 WebSearchAgent] 시작
   6.0s          [L3 WebSearchAgent] 🔧 search_web('AI 에이전트 기업 도입')
   7.1s          [L3 WebSearchAgent] 🔧 search_web('에이전트 도입 장애물')
   9.8s          [L3 WebSearchAgent] 완료 → 결과를 호출한 쪽으로 반환
  11.0s      [L2 ResearchAssistant] 🔧 SummarizerAgent('…')
  11.0s          [L3 SummarizerAgent] 시작
  13.5s          [L3 SummarizerAgent] 완료 → 결과를 호출한 쪽으로 반환
  15.2s      [L2 ResearchAssistant] 완료 → 결과를 호출한 쪽으로 반환
  16.0s  [L1 ReportWriter] 🔧 ResearchAssistant('AI 규제와 거버넌스')
   …
  58.3s  [L1 ReportWriter] 완료 → 최종 보고서 작성

######################################################################
📄 최종 보고서 (ReportWriter)
######################################################################

# 2026년 AI 트렌드 보고서
## 요약
…
💾 저장: reports/report_20261108_141530.md
```

> 위 시간, 하위 주제, 검색어는 예시입니다. 실제로는 LLM이 정하므로 실행할 때마다 달라집니다.
> 에이전트를 여러 번 거치므로 한 번 실행에 수십 번의 모델 호출이 일어날 수 있습니다(하위 주제 하나당 최소 6회, 3개면 ReportWriter 호출까지 약 20회 이상).
#### 검색 모드 비교

| | 기본 (가상 웹) | `--live` (실제 웹) |
|---|---|---|
| 검색 도구 | `search_web` — `data/web_corpus.json` 검색 | ADK 내장 `google_search` (Gemini 검색 그라운딩) |
| 인터넷 연결 | 모델 호출만 필요 | 모델 호출 + 실제 검색 |
| 결과 재현성 | 같은 검색어면 항상 같은 문서 | 시점에 따라 달라짐 |
| 수업 용도 | 패턴 구조 관찰, 결과 비교 | 실제 보고서 작성 |
| 주의 | 내용이 가상이므로 실제 사실로 인용 금지 | Gemini 모델에서만 동작, 검색 비용이 추가될 수 있음 |

`adk web`으로 실행할 때는 `--live` 대신 환경변수 `ADK_SEARCH_MODE=live`를 사용하세요.

### 다음에 다시 실행할 때

Step 1~3은 다시 할 필요 없습니다. 새 터미널에서는 아래 네 줄이면 됩니다.

```bash
cd 34_adk_decomposition
source .venv/bin/activate                # (.venv) 확인
export GOOGLE_API_KEY="..."              # ~/.zshrc에 넣어 두었다면 생략
python adk_hierarchical_report.py
```

---

## 모델 고르기 (키가 여러 개일 때)

키가 하나만 있으면 신경 쓸 필요 없습니다. 여러 개 설정되어 있으면 **Gemini → Claude → OpenAI** 순서로 자동 선택됩니다.

| 쓰는 키 | 기본 모델 | 추가 설치 |
|---|---|---|
| `GOOGLE_API_KEY` | `gemini-3.8-flash` | — |
| `ANTHROPIC_API_KEY` (Claude Code) | `claude-sonnet-5-5` | `pip install anthropic` |
| `OPENAI_API_KEY` (Codex) | `gpt-5.6` | `pip install openai` |

> 이 예제의 `--live`(실제 Google 검색)는 Gemini 내장 도구라 **Gemini 모델에서만** 동작합니다. Claude·OpenAI로는 기본 모드(가상 웹 검색)를 쓰세요. Claude·OpenAI로 `--live`를 주면 안내 메시지를 보여 주고 멈춥니다.

다른 것을 쓰려면 실행할 때 지정하세요.

```bash
# 공급자만 고르기 (기본 모델 사용)
ADK_PROVIDER=claude python adk_hierarchical_report.py
ADK_PROVIDER=openai python adk_hierarchical_report.py

# 모델 이름까지 직접 지정 (이름으로 공급자를 판단: claude-* → Claude, gpt-*/o* → OpenAI, 그 외 → Gemini)
ADK_MODEL=claude-opus-5-5 python adk_hierarchical_report.py
ADK_MODEL=gpt-5.6-luna    python adk_hierarchical_report.py
ADK_MODEL=gemini-3.5-flash-lite python adk_hierarchical_report.py
```

> **Claude를 Anthropic API 키로 쓸 때 주의**: ADK에 `model="claude-sonnet-5-5"`처럼 이름만 넘기면, ADK는 이것을 **Vertex AI(Google Cloud)의 Claude**로 연결해 Google Cloud 프로젝트를 요구합니다.
> 이 예제는 Anthropic API 키가 있으면 `AnthropicLlm(model=...)` 객체로 감싸서 Anthropic API로 직접 연결합니다(코드의 `resolve_model()` 참고).

## 웹 UI로 실행 (`adk web`)

```bash
mkdir -p report_agent
cp adk_hierarchical_report.py report_agent/agent.py
cp -r data report_agent/data
echo "from . import agent" > report_agent/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > report_agent/.env      # 또는 ANTHROPIC_API_KEY=... / OPENAI_API_KEY=...
adk web                              # 브라우저에서 http://localhost:8000 → report_agent 선택
```

채팅창에 `주제: 2026년 AI 트렌드`처럼 입력하세요. 웹 UI의 이벤트 화면에서는 `ResearchAssistant` 도구 호출과 그 결과가 보입니다. 그보다 아래 계층의 호출은 터미널의 트리 로그에서 확인할 수 있습니다.

> `adk web`은 에이전트 폴더의 `.env` 파일에서 키를 읽습니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 모델 공급자 | `export ADK_PROVIDER=gemini` / `claude` / `openai` | 설정된 키로 자동 감지 |
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` (또는 `claude-opus-5-5`, `gpt-5.6-luna` …) | 공급자별 기본 모델 |
| 공급자별 기본 모델 | 코드의 `DEFAULT_MODELS` | Gemini `gemini-3.8-flash` · Claude `claude-sonnet-5-5` · OpenAI `gpt-5.6` |
| 검색 모드 | `--live` 또는 `export ADK_SEARCH_MODE=live` | 가상 웹 |
| 기본 주제 | 코드의 `DEFAULT_TOPIC` | `2026년 AI 트렌드` |
| 하위 주제 개수·보고서 형식 | `ReportWriter`의 instruction | 3~4개, 제목/요약/섹션/시사점/출처 |
| 검색 결과 개수 | `search_web`의 `max_results` | 4 |

## 실습 과제 아이디어

1. **sub_agents vs AgentTool 비교**: ResearchAssistant의 `tools=[AgentTool(...), AgentTool(...)]`를 블로그처럼 `sub_agents=[web_searcher, summarizer]`로 바꿔 실행하세요. 트리 로그에서 SummarizerAgent가 사라지는 것과 보고서 품질이 달라지는 것을 확인해 보세요.
2. **계층 하나 더**: 섹션별로 사실 확인을 하는 `FactChecker`(Level 3)를 추가해 ResearchAssistant가 요약 후 검증까지 하도록 바꿔 보세요.
3. **병렬화 결합**: 하위 주제 조사를 하나씩 순서대로 하지 말고, `ParallelAgent`로 동시에 조사한 뒤 ReportWriter가 종합하도록 바꿔 보세요 (Parallel Fan-Out과 결합).
4. **컨텍스트 크기 관찰**: SummarizerAgent를 빼고 ResearchAssistant가 검색 원문을 그대로 반환하게 바꾼 뒤, 최상위 에이전트에 들어가는 텍스트 양이 얼마나 커지는지 비교해 보세요.

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
| `--live(실제 웹 검색)는 ... Gemini 모델에서만 동작합니다` | Claude·OpenAI로 실행 중. `--live` 없이 실행하거나 `ADK_PROVIDER=gemini`로 바꾸기 |
| `429 Resource exhausted` | 계층을 거치며 모델 호출이 많아 무료 등급 분당 한도에 걸릴 수 있음. 잠시 후 다시 실행하거나 하위 주제 수를 줄이기 |
| 보고서에 "추가 조사 필요"가 많음 | 가상 웹에 해당 주제 문서가 없음. 주제를 코퍼스 주제(위 표)에 맞추거나 `data/web_corpus.json`에 문서 추가 |
| ReportWriter가 직접 내용을 지어냄 | instruction의 "직접 검색하지 말고 ResearchAssistant를 호출" 문장을 강조하거나 더 강한 모델 사용 |
