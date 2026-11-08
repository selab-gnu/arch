# ADK Sequential Pipeline 예제 — PDF 처리 조립 라인

Google ADK(Agent Development Kit)로 구현한 **Sequential Pipeline(조립 라인) 패턴** 실습 예제입니다.
PDF 한 개를 받아 세 에이전트가 정해진 순서대로 **파싱 → 추출 → 요약**을 수행합니다.

> 원문: Google Developers Blog, [Developer's guide to multi-agent patterns in ADK](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
> 블로그의 ADK 의사코드를 실제로 실행되는 코드로 완성했습니다.

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
31_agent_patterns/
├── adk_sequential_pipeline.py   # 이 예제 (ADK Sequential Pipeline)
├── research_multi_agent.py      # (기존) LangChain Subagents 패턴 예제
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

## 설치

Python 3.10 이상이 필요합니다.

```bash
cd 31_agent_patterns
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -U google-adk pypdf fpdf2
```

- `google-adk`: 에이전트 프레임워크 (2.11.0에서 확인)
- `pypdf`: PDF 텍스트 추출
- `fpdf2`: `data/` 폴더가 없을 때 샘플 PDF를 즉석에서 만드는 용도 (선택)

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

> `python adk_sequential_pipeline.py`로 실행할 때는 위처럼 **터미널에서 export**해야 합니다.
> `adk web` / `adk run`으로 실행할 때는 에이전트 폴더(아래 `pdf_pipeline/`)의 `.env` 파일에 `GOOGLE_API_KEY=...`를 적어 두면 자동으로 읽습니다.
> 키가 담긴 `.env`는 git에 커밋하지 마세요.

## 실행

```bash
# 1) 기본 실행: data/invoice_en.pdf 처리
python adk_sequential_pipeline.py

# 2) 특정 PDF 처리
python adk_sequential_pipeline.py data/service_contract_ko.pdf

# 3) data 폴더의 PDF 4개를 차례로 모두 처리
python adk_sequential_pipeline.py data/

# 4) 내 PDF 처리 (여러 개 지정 가능)
python adk_sequential_pipeline.py ~/Documents/report.pdf ~/Downloads/receipt.pdf
```

### 출력 예시

실행하면 어느 에이전트가 어떤 도구를 호출했는지 순서대로 보여 준 뒤, 세션 상태에 저장된 결과를 출력합니다.

```
======================================================================
▶ 처리 중: .../data/service_contract_ko.pdf
======================================================================
[ParserAgent] 도구 호출 → pdf_parser
[ParserAgent] 완료 (753자)
[ExtractorAgent] 도구 호출 → regex_extractor
[ExtractorAgent] 완료 (…자)
[SummarizerAgent] 도구 호출 → summary_engine
[SummarizerAgent] 완료 (…자)

----- session.state['structured_data'] -----
{"document_type": "용역 계약서", "title": "AI 문서 처리 시스템 개발 용역 계약서",
 "dates": ["2026-11-01", "2026-11-15", "2027-03-31", ...],
 "amounts": ["₩85,000,000", "₩25,500,000", "₩34,000,000"], ...}

----- 최종 요약 (session.state['summary']) -----
(Gemini가 작성한 한국어 요약)
```

> 구조화 데이터와 요약의 문장은 LLM이 생성하므로 실행할 때마다 표현이 조금씩 달라질 수 있습니다.
> 위 정규식 추출 결과(날짜·금액·연락처)는 도구가 계산하므로 항상 같습니다.

### 웹 UI로 실행 (`adk web`)

ADK 개발 UI에서 이벤트·상태 변화를 눈으로 확인하려면 에이전트 폴더 구조가 필요합니다.

```bash
mkdir -p pdf_pipeline
cp adk_sequential_pipeline.py pdf_pipeline/agent.py
echo "from . import agent" > pdf_pipeline/__init__.py
echo "GOOGLE_API_KEY=발급받은_키" > pdf_pipeline/.env
adk web                              # 브라우저에서 http://localhost:8000 → pdf_pipeline 선택
```

채팅창에 `다음 PDF를 처리해 주세요: /절대경로/31_agent_patterns/data/invoice_en.pdf`처럼 **PDF의 절대 경로**를 입력하세요. 오른쪽 State 탭에서 `raw_text → structured_data → summary`가 차례로 채워지는 것을 볼 수 있습니다.

## 설정 바꾸기

| 항목 | 방법 | 기본값 |
|---|---|---|
| 사용 모델 | `export ADK_MODEL=gemini-3.5-flash-lite` | `gemini-3.8-flash` |
| LLM에 넘길 PDF 텍스트 최대 길이 | 코드의 `MAX_CHARS` | 20,000자 |
| 추출할 항목 | 코드의 `_PATTERNS` 딕셔너리에 정규식 추가 | 이메일·URL·날짜·금액·전화·퍼센트 |

## 샘플 데이터 수정·추가하기

`data/src/*.html`을 고친 뒤 LibreOffice로 PDF를 다시 만들 수 있습니다.

```bash
# macOS: brew install --cask libreoffice
soffice --headless --convert-to pdf --outdir data data/src/*.html
```

LibreOffice가 없으면 HTML을 브라우저로 열어 **인쇄 → PDF로 저장**해도 됩니다.
직접 만든 PDF를 `data/`에 넣으면 `python adk_sequential_pipeline.py data/`로 함께 처리됩니다.

> 텍스트 PDF만 지원합니다. 스캔 이미지 PDF는 글자를 읽을 수 없으므로 OCR이 먼저 필요합니다.

## 문제 해결

| 증상 | 원인과 해결 |
|---|---|
| `ModuleNotFoundError: google.adk` | 가상환경을 활성화했는지 확인하고 `pip install -U google-adk` |
| API 키·인증 관련 오류 | `GOOGLE_API_KEY`(또는 Vertex AI 환경변수)가 현재 터미널에 설정되어 있는지 `echo $GOOGLE_API_KEY`로 확인 |
| `404 ... model not found` | 사용 가능한 모델 ID로 `ADK_MODEL` 변경 (Google AI Studio의 모델 목록 참고) |
| `KeyError: 'raw_text'` 같은 상태 키 오류 | 앞 단계 에이전트가 응답하지 못해 state 키가 비어 있음. 위쪽 로그에서 실패한 단계 확인 |
| 요약에 `ERROR: 파일이 없습니다` | PDF 경로 오타. 상대 경로 대신 절대 경로로 시도 |
| 한글 금액 `1,250억 원`이 정규식에 안 잡힘 | 현재 정규식은 `원` 바로 앞의 숫자만 인식. 이런 값은 ExtractorAgent(LLM)가 원문을 보고 보완 |

## 실습 과제 아이디어

1. **단계 추가**: 요약을 영어로 번역하는 `TranslatorAgent`를 네 번째 단계로 추가해 보세요 (`{summary}`를 읽도록).
2. **출력 스키마**: `ExtractorAgent`에 Pydantic 모델로 `output_schema`를 지정해 JSON 형식을 강제해 보세요.
3. **패턴 확장**: 회의록·계약서·인보이스를 구분해 서로 다른 추출 에이전트로 보내도록 앞단에 Coordinator(라우터)를 붙여 보세요 → Coordinator/Dispatcher 패턴.
4. **병렬화**: 정규식 추출과 LLM 엔티티 추출을 `ParallelAgent`로 동시에 돌린 뒤 합쳐 보세요 → Parallel Fan-Out/Gather 패턴.
