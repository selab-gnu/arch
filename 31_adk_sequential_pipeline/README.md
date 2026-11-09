# ADK Sequential Pipeline 예제 — PDF 처리 조립 라인

Google ADK(Agent Development Kit)로 구현한 **Sequential Pipeline(조립 라인) 패턴** 실습 예제입니다.
PDF 한 개를 받아 세 에이전트가 정해진 순서대로 **파싱 → 추출 → 요약**을 수행합니다.

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
7. [샘플 데이터 수정·추가하기](#샘플-데이터-수정추가하기)
8. [실습 과제 아이디어](#실습-과제-아이디어)
9. [문제 해결](#문제-해결)

## 구조

```
사용자 ──"이 PDF를 처리해 줘"──▶ SequentialAgent (PDFProcessingPipeline)
                                  │
   ① ParserAgent      ── pdf_parser 도구 ────────▶ state["raw_text"]
                                  │
   ② ExtractorAgent   ── regex_extractor 도구 ───▶ state["structured_data"]   ← instruction의 {raw_text}
                                  │
   ③ SummarizerAgent  ── summary_engine 도구 ────▶ state["summary"]           ← instruction의 {structured_data}
```

| 단계 | 에이전트 | 도구 (블로그 이름) | 하는 일 | 결과 저장 위치 |
|---|---|---|---|---|
| 1 | `ParserAgent` | `pdf_parser` (PDFParser) | pypdf로 PDF 텍스트 추출 | `raw_text` |
| 2 | `ExtractorAgent` | `regex_extractor` (RegexExtractor) | 정규식으로 이메일·URL·날짜·금액·전화·퍼센트를 뽑은 뒤, LLM이 JSON으로 구조화 | `structured_data` |
| 3 | `SummarizerAgent` | `summary_engine` (SummaryEngine) | 구조화 데이터의 통계를 확인하고 한국어 요약 작성 | `summary` |

**핵심 포인트**

- **`output_key`**: 각 에이전트의 최종 응답이 `session.state`의 해당 키에 자동으로 저장됩니다.
- **`{raw_text}`, `{structured_data}`**: instruction 안의 중괄호는 실행할 때 `session.state` 값으로 자동 치환됩니다. 앞 단계의 결과가 이렇게 다음 단계로 전달됩니다.
- **`SequentialAgent`**: `sub_agents`를 적힌 순서대로 한 번씩 실행합니다. 흐름이 결정적이라 디버깅이 쉽습니다.

## 폴더 구성

```
31_adk_sequential_pipeline/
├── adk_sequential_pipeline.py   # 이 예제의 핵심: 세 에이전트 + SequentialAgent 조립 라인 + 실행(main)
├── pdf_tools.py                 # 에이전트가 쓰는 도구: pdf_parser / regex_extractor / summary_engine
├── model_config.py              # API 키에 맞춰 Gemini / Claude / OpenAI 모델 자동 선택 (resolve_model)
├── pdf_inputs.py                # 명령행 인자 → 처리할 PDF 목록, 샘플 PDF 생성
├── error_messages.py            # 서버 과부하·요청 한도 같은 일시적 오류 안내 문구
├── tests/                       # 동작 고정용 테스트 (pytest, 네트워크·API 키 불필요)
├── README.md
└── data/                        # 실습용 샘플 PDF
    ├── invoice_en.pdf           # 영문 클라우드 서비스 인보이스 (1쪽)
    ├── meeting_minutes_ko.pdf   # 프로젝트 주간 회의록 (1쪽)
    ├── research_report_ko.pdf   # 멀티 에이전트 도입 효과 분석 보고서 (2쪽)
    ├── service_contract_ko.pdf  # 개발 용역 계약서 (1쪽)
    └── src/                     # 위 PDF의 HTML 원본 (수정 후 다시 PDF로 만들 수 있음)
```

샘플 데이터는 모두 가상의 내용이며, 추출 대상(날짜·금액·연락처·퍼센트·URL)이 골고루 들어가도록 만들었습니다.

| 파일 | 언어 | 주요 추출 대상 |
|---|---|---|
| `invoice_en.pdf` | 영어 | 청구 항목·소계·세금·총액($4,339.50), 지급 기한, 결제 URL |
| `meeting_minutes_ko.pdf` | 한국어 | 담당자별 할 일과 기한(표), 예산(₩, 원), 휴대폰 번호 |
| `research_report_ko.pdf` | 한국어 | 패턴별 도입 비율(표), 조사 기간, 참고 URL — **여러 쪽 문서** |
| `service_contract_ko.pdf` | 한국어 | 계약 당사자, 계약 기간, 선금·중도금·잔금과 지급일 |

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
cd 31_adk_sequential_pipeline

conda deactivate                   # 프롬프트 앞에 (base)가 보이면 먼저 빠져나오기 (Anaconda 사용자만)
python3 -m venv .venv              # 가상환경 만들기 (처음 한 번)
source .venv/bin/activate          # 가상환경 켜기   (Windows: .venv\Scripts\activate)
```

✅ **확인**: 프롬프트 맨 앞에 `(.venv)`가 붙고, 아래 명령의 경로가 이 폴더의 `.venv` 안을 가리키면 성공입니다.

```bash
which python                       # …/31_adk_sequential_pipeline/.venv/bin/python
```

### Step 2. 패키지 설치하기

```bash
pip install -U google-adk pypdf fpdf2

# 사용할 모델에 따라 하나 더 설치 (Gemini만 쓰면 생략)
pip install -U anthropic           # Claude (Anthropic API 키)
pip install -U openai              # OpenAI GPT (OpenAI API 키)
```

| 패키지 | 용도 |
|---|---|
| `google-adk` | 에이전트 프레임워크 (2.11.0에서 확인) |
| `pypdf` | PDF 텍스트 추출 |
| `fpdf2` | `data/` 폴더가 없을 때 샘플 PDF를 즉석에서 만드는 용도 (선택) |
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

```bash
python adk_sequential_pipeline.py
```

✅ **확인**: 첫 줄에 어떤 모델로 실행되는지 표시됩니다. 설정한 키에 맞는 모델이 나오면 정상입니다.

```
🧠 사용 모델: Gemini (gemini-3.8-flash)
```

다른 PDF로도 실행해 보세요.

```bash
python adk_sequential_pipeline.py data/service_contract_ko.pdf             # 특정 PDF
python adk_sequential_pipeline.py data/                                    # data 폴더의 PDF 4개를 모두
python adk_sequential_pipeline.py ~/Documents/report.pdf ~/Downloads/a.pdf # 내 PDF (여러 개 가능)
```

### Step 6. 결과 확인하기

실행하면 세 에이전트가 **순서대로** 도구를 호출한 기록이 나오고, 마지막에 세션 상태에 저장된 결과가 출력됩니다.

```
🧠 사용 모델: Gemini (gemini-3.8-flash)

======================================================================
▶ 처리 중: .../data/service_contract_ko.pdf
======================================================================
[ParserAgent] 도구 호출 → pdf_parser            ← ① 파싱
[ParserAgent] 완료 (753자)
[ExtractorAgent] 도구 호출 → regex_extractor    ← ② 추출
[ExtractorAgent] 완료 (…자)
[SummarizerAgent] 도구 호출 → summary_engine    ← ③ 요약
[SummarizerAgent] 완료 (…자)

----- session.state['structured_data'] -----
{"document_type": "용역 계약서", "title": "AI 문서 처리 시스템 개발 용역 계약서",
 "dates": ["2026-11-01", "2026-11-15", "2027-03-31", ...],
 "amounts": ["₩85,000,000", "₩25,500,000", "₩34,000,000"], ...}

----- 최종 요약 (session.state['summary']) -----
(LLM이 작성한 한국어 요약)
```

**관찰 포인트**

- `[ParserAgent] → [ExtractorAgent] → [SummarizerAgent]` 순서가 **항상 같습니다**. 이것이 Sequential Pipeline입니다.
- `structured_data`에 앞 단계의 `raw_text`가 반영되어 있는지 확인해 보세요(상태를 통한 전달).

> 구조화 데이터와 요약의 문장은 LLM이 생성하므로 실행할 때마다 표현이 조금씩 달라질 수 있습니다.
> 정규식 추출 결과(날짜·금액·연락처)는 도구가 계산하므로 항상 같습니다.

### 다음에 다시 실행할 때

Step 1~3은 다시 할 필요 없습니다. 새 터미널에서는 아래 세 줄이면 됩니다.

```bash
cd 31_adk_sequential_pipeline
source .venv/bin/activate                # (.venv) 확인
export GOOGLE_API_KEY="..."              # ~/.zshrc에 넣어 두었다면 생략
python adk_sequential_pipeline.py
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
ADK_PROVIDER=claude python adk_sequential_pipeline.py
ADK_PROVIDER=openai python adk_sequential_pipeline.py

# 모델 이름까지 직접 지정 (이름으로 공급자를 판단: claude-* → Claude, gpt-*/o* → OpenAI, 그 외 → Gemini)
ADK_MODEL=claude-opus-5-5 python adk_sequential_pipeline.py
ADK_MODEL=gpt-5.6-luna    python adk_sequential_pipeline.py
ADK_MODEL=gemini-3.5-flash-lite python adk_sequential_pipeline.py
```

> **Claude를 Anthropic API 키로 쓸 때 주의**: ADK에 `model="claude-sonnet-5-5"`처럼 이름만 넘기면, ADK는 이것을 **Vertex AI(Google Cloud)의 Claude**로 연결해 Google Cloud 프로젝트를 요구합니다.
> 이 예제는 Anthropic API 키가 있으면 `AnthropicLlm(model=...)` 객체로 감싸서 Anthropic API로 직접 연결합니다(`model_config.py`의 `resolve_model()` 참고). 직접 코드를 짤 때도 이 점을 기억하세요.

## 웹 UI로 실행 (`adk web`)

ADK 개발 UI에서 이벤트·상태 변화를 눈으로 확인하려면 에이전트 폴더 구조가 필요합니다.

```bash
mkdir -p pdf_pipeline
# 코드가 여러 파일로 나뉘어 있으므로 복사하지 않고, 예제 폴더의 root_agent를 불러오는 agent.py를 만듭니다.
cat > pdf_pipeline/agent.py <<'EOF'
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 예제 폴더(31_adk_sequential_pipeline)
from adk_sequential_pipeline import root_agent  # noqa: E402,F401
EOF
echo "from . import agent" > pdf_pipeline/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > pdf_pipeline/.env      # 또는 ANTHROPIC_API_KEY=... / OPENAI_API_KEY=...
adk web                              # 브라우저에서 http://localhost:8000 → pdf_pipeline 선택
```

채팅창에 `다음 PDF를 처리해 주세요: /절대경로/31_adk_sequential_pipeline/data/invoice_en.pdf`처럼 **PDF의 절대 경로**를 입력하세요. 오른쪽 State 탭에서 `raw_text → structured_data → summary`가 차례로 채워지는 것을 볼 수 있습니다.

> `adk web`은 에이전트 폴더의 `.env` 파일에서 키를 읽습니다. 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 모델 공급자 | `export ADK_PROVIDER=gemini` / `claude` / `openai` | 설정된 키로 자동 감지 |
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` (또는 `claude-opus-5-5`, `gpt-5.6-luna` …) | 공급자별 기본 모델 |
| 공급자별 기본 모델 | `model_config.py`의 `DEFAULT_MODELS` | Gemini `gemini-3.8-flash` · Claude `claude-sonnet-5-5` · OpenAI `gpt-5.6` |
| LLM에 넘길 PDF 텍스트 최대 길이 | `pdf_tools.py`의 `MAX_CHARS` | 20,000자 |
| 추출할 항목 | `pdf_tools.py`의 `_PATTERNS` 딕셔너리에 정규식 추가 | 이메일·URL·날짜·금액·전화·퍼센트 |

## 샘플 데이터 수정·추가하기

`data/src/*.html`을 고친 뒤 LibreOffice로 PDF를 다시 만들 수 있습니다.

```bash
# macOS: brew install --cask libreoffice
soffice --headless --convert-to pdf --outdir data data/src/*.html
```

LibreOffice가 없으면 HTML을 브라우저로 열어 **인쇄 → PDF로 저장**해도 됩니다.
직접 만든 PDF를 `data/`에 넣으면 `python adk_sequential_pipeline.py data/`로 함께 처리됩니다.

> 텍스트 PDF만 지원합니다. 스캔 이미지 PDF는 글자를 읽을 수 없으므로 OCR이 먼저 필요합니다.

## 실습 과제 아이디어

1. **단계 추가**: 요약을 영어로 번역하는 `TranslatorAgent`를 네 번째 단계로 추가해 보세요 (`{summary}`를 읽도록).
2. **출력 스키마**: `ExtractorAgent`에 Pydantic 모델로 `output_schema`를 지정해 JSON 형식을 강제해 보세요.
3. **패턴 확장**: 회의록·계약서·인보이스를 구분해 서로 다른 추출 에이전트로 보내도록 앞단에 Coordinator(라우터)를 붙여 보세요 → Coordinator/Dispatcher 패턴.
4. **병렬화**: 정규식 추출과 LLM 엔티티 추출을 `ParallelAgent`로 동시에 돌린 뒤 합쳐 보세요 → Parallel Fan-Out/Gather 패턴.
5. **모델 비교**: 같은 PDF를 `ADK_PROVIDER=gemini`, `claude`, `openai`로 각각 실행해 구조화 데이터(JSON)의 정확도와 요약 품질을 비교해 보세요. 에이전트마다 다른 모델을 써 보는 것도 가능합니다(예: 파싱은 가벼운 모델, 요약은 큰 모델).

## 문제 해결

**설치·환경 (Step 1~2)**

| 증상 | 원인과 해결 |
|---|---|
| `pip's dependency resolver ... incompatible` (예: `mlflow ... requires starlette<1`) | 기존 환경(Anaconda `base` 등)에 설치해서 다른 패키지와 충돌. `conda deactivate` 후 [Step 1](#step-1-가상환경-만들기)대로 **가상환경을 따로 만들어** 설치 |
| 프롬프트에 `(.venv)`가 없음 / `which python`이 `/opt/anaconda3/...` | 가상환경이 꺼져 있음. 이 폴더에서 `source .venv/bin/activate` |
| `ModuleNotFoundError: google.adk` | 가상환경을 켜지 않았거나 설치 전. `source .venv/bin/activate` 후 `pip install -U google-adk` |
| `Claude를 쓰려면 anthropic 패키지가 필요합니다` | `pip install -U anthropic` |
| `OpenAI 모델을 쓰려면 openai 패키지가 필요합니다` | `pip install -U openai` |

**API 키 (Step 3~4)**

| 증상 | 원인과 해결 |
|---|---|
| `API 키가 설정되어 있지 않습니다` | `echo $GOOGLE_API_KEY $ANTHROPIC_API_KEY $OPENAI_API_KEY`로 현재 터미널에 키가 있는지 확인. 새 터미널을 열었다면 `export`를 다시 하거나 `~/.zshrc`에 등록 |
| `❌ API 키 인증 실패` (`Unauthorized`, `401`) | 키 값 오타, 만료된 키, 또는 **구독 로그인 정보를 키로 착각**한 경우. [Step 3](#step-3-api-키-발급받기)의 페이지에서 API 키를 새로 발급 |
| 의도와 다른 모델이 선택됨 | 키가 여러 개 설정됨. `ADK_PROVIDER=claude`처럼 직접 지정 ([모델 고르기](#모델-고르기-키가-여러-개일-때)) |

**실행 중 (Step 5~6)**

| 증상 | 원인과 해결 |
|---|---|
| `503 UNAVAILABLE` / `high demand` / `⏳ 모델 서버가 일시적으로 응답하지 못했습니다` | 코드 문제가 아니라 모델 서버의 일시적 과부하. Gemini는 자동으로 최대 6번(약 1분) 재시도하며, 그래도 실패하면 이 안내가 나옴. 1~2분 뒤 다시 실행하거나 `ADK_MODEL=gemini-3.5-flash-lite`처럼 가벼운 모델, 또는 `ADK_PROVIDER=claude`/`openai`로 다른 공급자 사용 |
| `404 ... model not found` / `model_not_found` | 계정에서 쓸 수 없는 모델 이름. 각 공급자의 모델 목록에서 확인해 `ADK_MODEL`로 지정 |
| `400 … Function tools with reasoning_effort are not supported … use /v1/responses` (OpenAI) | 이전 버전 코드에서 OpenAI를 예전 Chat Completions 방식으로 연결해서 생긴 오류. 최신 코드는 Responses API(`OpenAIResponsesLlm`)로 연결하므로 코드 파일을 최신으로 바꾸면 해결 |
| `KeyError: 'raw_text'` 같은 상태 키 오류 | 앞 단계 에이전트가 응답하지 못해 state 키가 비어 있음. 위쪽 로그에서 실패한 단계 확인 |
| 요약에 `ERROR: 파일이 없습니다` | PDF 경로 오타. 상대 경로 대신 절대 경로로 시도 |
| 한글 금액 `1,250억 원`이 정규식에 안 잡힘 | 현재 정규식은 `원` 바로 앞의 숫자만 인식. 이런 값은 ExtractorAgent(LLM)가 원문을 보고 보완 |
