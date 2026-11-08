"""
PDF 처리 파이프라인 예제 (Google ADK - Sequential Pipeline 패턴, "조립 라인")

출처: Google Developers Blog, "Developer's guide to multi-agent patterns in ADK"
      https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/
      블로그의 의사코드(PDFParser / RegexExtractor / SummaryEngine)를 실제 동작하는 도구로 구현했습니다.

구조:
    사용자 → [SequentialAgent: PDFProcessingPipeline]
               ① ParserAgent     --(output_key="raw_text")-------→ session.state
               ② ExtractorAgent  --(output_key="structured_data")→ session.state   ({raw_text} 읽음)
               ③ SummarizerAgent --(output_key="summary")--------→ 최종 요약      ({structured_data} 읽음)

설치:
    pip install -U google-adk pypdf fpdf2      # fpdf2는 샘플 PDF 생성용
    pip install -U anthropic                   # Claude를 쓸 때만
    pip install -U openai                      # OpenAI GPT를 쓸 때만

API 키 (아래 중 하나만 있으면 자동으로 감지해 해당 모델을 사용):
    export GOOGLE_API_KEY=...       # Gemini      — https://aistudio.google.com
    export ANTHROPIC_API_KEY=...    # Claude      — Claude Code에서 쓰는 Anthropic API 키 (pip install anthropic)
    export OPENAI_API_KEY=...       # OpenAI GPT  — Codex에서 쓰는 OpenAI API 키 (pip install openai)
    # 또는 Vertex AI: export GOOGLE_GENAI_USE_VERTEXAI=TRUE GOOGLE_CLOUD_PROJECT=... GOOGLE_CLOUD_LOCATION=...
    키가 여러 개면 ADK_PROVIDER=gemini|claude|openai 로 고르고, 모델은 ADK_MODEL 로 직접 지정할 수 있습니다.

실행: (자세한 사용법은 README.md 참고)
    python adk_sequential_pipeline.py                         # data/invoice_en.pdf 처리
    python adk_sequential_pipeline.py data/service_contract_ko.pdf
    python adk_sequential_pipeline.py data/                   # data 폴더의 PDF 전체 처리
    python adk_sequential_pipeline.py ~/Documents/my.pdf      # 내 PDF 처리

모델 지정 예) export ADK_MODEL=gemini-3.5-flash-lite / claude-opus-5-5 / gpt-5.6-luna
"""

import asyncio
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

# 실습 화면을 깔끔하게: ADK의 실험 기능·deprecated 안내와 내부 로그는 숨깁니다 (오류는 그대로 표시).
import logging
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module=r"google\.adk")
warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")
warnings.filterwarnings("ignore", message=r".*deprecated in favor of Workflow")
logging.getLogger("google_adk").setLevel(logging.CRITICAL)  # ADK 내부의 중복 오류 로그 숨김 (예외 자체는 그대로 전달됨)


# ---------------------------------------------------------------------------
# 모델 선택 — Gemini / Claude / OpenAI 중 '가지고 있는 API 키'에 맞춰 자동으로 고릅니다.
#   우선순위: ADK_MODEL(직접 지정) > ADK_PROVIDER(공급자 지정) > 설정된 키 자동 감지(Gemini → Claude → OpenAI)
# ---------------------------------------------------------------------------
DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "claude": "claude-sonnet-5-5",
    "openai": "gpt-5.6",
}


def _has_key(provider: str) -> bool:
    env = os.environ
    return {
        "gemini": bool(env.get("GOOGLE_API_KEY") or env.get("GEMINI_API_KEY")
                       or env.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true")),
        "claude": bool(env.get("ANTHROPIC_API_KEY")),
        "openai": bool(env.get("OPENAI_API_KEY")),
    }[provider]


def _provider_of(model_name: str) -> str:
    if model_name.startswith("claude-"):
        return "claude"
    if re.match(r"(gpt-|o\d)", model_name):
        return "openai"
    return "gemini"


def resolve_model():
    """ADK에 넘길 모델을 고릅니다. 반환값: (model, 설명 문자열)

    - Gemini, OpenAI: 모델 이름 문자열만 넘기면 ADK가 알아서 연결합니다
      (gpt-* 이름은 ADK의 OpenAI 연결로 처리되며 OPENAI_API_KEY를 사용).
    - Claude: 'claude-...' 문자열만 넘기면 ADK는 'Vertex AI의 Claude'로 연결해 Google Cloud 프로젝트를 요구합니다.
      Anthropic API 키(ANTHROPIC_API_KEY)로 직접 쓰려면 AnthropicLlm 객체로 감싸야 합니다.
    """
    name = os.environ.get("ADK_MODEL", "").strip()
    provider = os.environ.get("ADK_PROVIDER", "").strip().lower()
    if provider and provider not in DEFAULT_MODELS:
        raise SystemExit(f"ADK_PROVIDER는 {', '.join(DEFAULT_MODELS)} 중 하나여야 합니다 (현재: {provider}).")

    if name:
        provider = provider or _provider_of(name)
    else:
        if not provider:
            provider = next((p for p in DEFAULT_MODELS if _has_key(p)), "gemini")
        name = DEFAULT_MODELS[provider]

    vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true")
    if provider == "claude" and not vertex:
        try:
            from google.adk.models.anthropic_llm import AnthropicLlm
        except ImportError:
            raise SystemExit("Claude를 쓰려면 anthropic 패키지가 필요합니다:  pip install -U anthropic")
        return AnthropicLlm(model=name), f"Claude ({name}, Anthropic API 키)"
    if provider == "openai":
        try:
            import openai  # noqa: F401
        except ImportError:
            raise SystemExit("OpenAI 모델을 쓰려면 openai 패키지가 필요합니다:  pip install -U openai")
        return name, f"OpenAI ({name}, OpenAI API 키)"
    if provider == "claude":
        return name, f"Claude ({name}, Vertex AI)"
    # Gemini는 일시적 오류(요청 폭주 503, 한도 429 등)에서 자동으로 재시도하도록 설정합니다.
    from google.adk.models.google_llm import Gemini
    from google.genai import types as _gtypes
    gemini = Gemini(model=name, retry_options=_gtypes.HttpRetryOptions(
        attempts=6, initial_delay=2, max_delay=30, exp_base=2,
        http_status_codes=[408, 429, 500, 502, 503, 504]))
    return gemini, f"Gemini ({name})"


MODEL, MODEL_LABEL = resolve_model()
APP_NAME = "pdf_pipeline_app"
MAX_CHARS = 20_000  # LLM에 넘길 PDF 텍스트 최대 길이 (긴 문서는 잘라서 사용)


# ---------------------------------------------------------------------------
# 도구(Tools) — 블로그의 PDFParser / RegexExtractor / SummaryEngine 구현
#   ADK는 일반 파이썬 함수를 도구로 자동 변환합니다. 타입 힌트와 docstring이
#   LLM에게 보이는 '도구 설명서'가 되므로 정확하게 작성하는 것이 중요합니다.
# ---------------------------------------------------------------------------
def pdf_parser(file_path: str) -> dict:
    """PDF 파일에서 텍스트를 추출합니다.

    Args:
        file_path: 읽을 PDF 파일 경로.

    Returns:
        status, page_count, text(추출된 원문)를 담은 dict.
    """
    from pypdf import PdfReader

    path = Path(file_path).expanduser()
    if not path.exists():
        return {"status": "error", "message": f"파일이 없습니다: {path}"}
    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    truncated = len(text) > MAX_CHARS
    return {
        "status": "success",
        "page_count": len(reader.pages),
        "truncated": truncated,
        "text": text[:MAX_CHARS],
    }


_PATTERNS = {
    # 한글은 정규식에서 '단어 문자'라서 \b 경계가 생기지 않습니다(예: "2026-11-15부터").
    # 그래서 \b 대신 (?<!\d) / (?!\d) 로 숫자 경계를 지정합니다.
    "emails": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "urls": r"https?://[^\s)>\]]+",
    "dates": r"(?<!\d)\d{4}[-./]\d{1,2}[-./]\d{1,2}(?!\d)|(?<!\d)\d{1,2}/\d{1,2}/\d{4}(?!\d)",
    "amounts": r"[$€£₩][ \t]?\d[\d,]*(?:\.\d+)?|(?<![\d.])\d[\d,]*(?:\.\d+)?[ \t]?(?:USD|KRW|EUR|원)",
    "phones": r"(?<![\d-])(?:\+\d{1,3}[-\s])?\(?\d{2,4}\)?[-\s]\d{3,4}[-\s]\d{4}(?![\d-])",
    "percentages": r"(?<![\d.])\d+(?:\.\d+)?[ \t]?%",
}


def regex_extractor(text: str) -> dict:
    """정규식으로 텍스트에서 이메일·URL·날짜·금액·전화번호·퍼센트를 추출합니다.

    Args:
        text: 분석할 원문 텍스트.

    Returns:
        항목별로 중복을 제거한 추출 결과 목록을 담은 dict.
    """
    result = {}
    for name, pattern in _PATTERNS.items():
        found = [m.strip().rstrip(".,") for m in re.findall(pattern, text)]
        result[name] = list(dict.fromkeys(found))  # 순서 유지 중복 제거
    return {"status": "success", "entities": result}


def summary_engine(structured_data: str) -> dict:
    """구조화된 데이터(JSON 문자열)의 통계를 계산해 요약 작성을 돕습니다.

    Args:
        structured_data: ExtractorAgent가 만든 JSON 형식의 구조화 데이터.

    Returns:
        항목 개수, 최상위 키 목록, 금액 값 목록과 최댓값(보통 총액)을 담은 dict.
    """
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", structured_data.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"status": "error", "message": "JSON으로 해석할 수 없습니다. 원문을 바탕으로 요약하세요."}

    def walk(obj, counter):
        if isinstance(obj, dict):
            for k, v in obj.items():
                counter[k] += len(v) if isinstance(v, list) else 1
                walk(v, counter)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, counter)

    counts = Counter()
    walk(data, counts)
    # 소계·세금·총액이 함께 들어 있는 경우가 많으므로 합산하지 않고 값과 최댓값만 알려 줍니다.
    raw_amounts = data.get("amounts", []) if isinstance(data, dict) else []
    values = [float(a.replace(",", "")) for a in re.findall(r"\d[\d,]*(?:\.\d+)?", json.dumps(raw_amounts))]
    return {
        "status": "success",
        "top_level_keys": list(data.keys()) if isinstance(data, dict) else [],
        "field_counts": dict(counts.most_common(15)),
        "amount_values": values,
        "max_amount": max(values) if values else None,  # 보통 총액(Total)에 해당
    }


# ---------------------------------------------------------------------------
# 1) ParserAgent — PDF를 읽어 원문을 state["raw_text"]에 저장
# ---------------------------------------------------------------------------
parser = LlmAgent(
    name="ParserAgent",
    model=MODEL,
    description="PDF를 파싱해 원문 텍스트를 추출합니다.",
    instruction=(
        "Parse raw PDF and extract text.\n"
        "사용자 메시지에 있는 PDF 경로로 pdf_parser 도구를 호출하세요.\n"
        "도구가 반환한 text를 수정·요약하지 말고 그대로 출력하세요. 다른 말은 덧붙이지 마세요.\n"
        "도구가 error를 반환하면 'ERROR: <메시지>'만 출력하세요."
    ),
    tools=[pdf_parser],
    output_key="raw_text",  # 이 에이전트의 최종 응답 → session.state["raw_text"]
)

# ---------------------------------------------------------------------------
# 2) ExtractorAgent — {raw_text}를 읽어 구조화 데이터를 state["structured_data"]에 저장
#    instruction 안의 {raw_text}는 실행 시 session.state 값으로 자동 치환됩니다.
# ---------------------------------------------------------------------------
extractor = LlmAgent(
    name="ExtractorAgent",
    model=MODEL,
    description="원문에서 구조화된 데이터를 추출합니다.",
    instruction=(
        "Extract structured data from {raw_text}.\n\n"
        "1. 먼저 위 원문 전체를 text 인자로 regex_extractor 도구를 호출하세요.\n"
        "2. 도구 결과와 원문을 함께 보고, 아래 키를 가진 JSON 하나만 출력하세요.\n"
        '   {"document_type": str, "title": str, "parties": [str], "dates": [str], '
        '"amounts": [str], "contacts": {"emails": [str], "phones": [str], "urls": [str]}, '
        '"key_facts": [str]}\n'
        "3. 원문에 없는 값은 빈 문자열/빈 목록으로 두고 지어내지 마세요. JSON 외의 텍스트는 출력하지 마세요."
    ),
    tools=[regex_extractor],
    output_key="structured_data",
)

# ---------------------------------------------------------------------------
# 3) SummarizerAgent — {structured_data}를 읽어 최종 요약 작성
# ---------------------------------------------------------------------------
summarizer = LlmAgent(
    name="SummarizerAgent",
    model=MODEL,
    description="구조화 데이터로 사람이 읽을 요약을 작성합니다.",
    instruction=(
        "Generate summary from {structured_data}.\n\n"
        "먼저 위 JSON을 그대로 structured_data 인자로 summary_engine 도구를 호출해 통계를 확인하세요.\n"
        "그다음 한국어로 요약을 작성하세요.\n"
        "형식: 문서 종류와 제목 한 줄 / 핵심 내용 3~5개 bullet / 주요 날짜·금액 / 연락처\n"
        "구조화 데이터에 없는 내용은 추측하지 마세요."
    ),
    tools=[summary_engine],
    output_key="summary",
)

# ---------------------------------------------------------------------------
# 4) 조립 라인 — SequentialAgent가 세 에이전트를 정해진 순서로 실행
# ---------------------------------------------------------------------------
pipeline = SequentialAgent(
    name="PDFProcessingPipeline",
    sub_agents=[parser, extractor, summarizer],
)

root_agent = pipeline  # `adk web` / `adk run` 으로 실행할 때 쓰는 이름


# ---------------------------------------------------------------------------
# 샘플 PDF 생성 (PDF를 지정하지 않았을 때만 사용)
# ---------------------------------------------------------------------------
def make_sample_pdf(path: Path) -> Path:
    from fpdf import FPDF

    lines = [
        "INVOICE  #INV-2026-1108",
        "Issue date: 2026-11-08    Due date: 2026-12-08",
        "From: Acme Cloud Services Inc. (billing@acmecloud.example, +1-415-555-0142)",
        "To: Gyeongsang Software Lab",
        "",
        "Items:",
        "  - GPU compute (A100, 120 hours) ........ $3,600.00",
        "  - Object storage (2 TB, 1 month) ....... $46.00",
        "  - Premium support plan ................. $299.00",
        "",
        "Subtotal: $3,945.00   Tax (10%): $394.50   Total due: $4,339.50",
        "Pay online at https://pay.acmecloud.example/inv-2026-1108",
        "Late payments incur a 1.5% monthly fee.",
    ]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))
    return path


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------
async def run_pipeline(pdf_path: str) -> dict:
    runner = InMemoryRunner(agent=pipeline, app_name=APP_NAME)
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id="user")

    message = types.Content(role="user", parts=[types.Part(text=f"다음 PDF를 처리해 주세요: {pdf_path}")])

    # 이벤트를 스트리밍하면 조립 라인이 어떤 순서로 움직이는지 볼 수 있습니다.
    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=message):
        for call in event.get_function_calls() or []:
            print(f"[{event.author}] 도구 호출 → {call.name}")
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts)
            print(f"[{event.author}] 완료 ({len(text)}자)")

    final = await runner.session_service.get_session(app_name=APP_NAME, user_id="user", session_id=session.id)
    return final.state


DATA_DIR = Path(__file__).with_name("data")


def collect_pdfs(args: list[str]) -> list[Path]:
    """명령행 인자(파일 또는 폴더)를 PDF 경로 목록으로 바꿉니다. 인자가 없으면 data/invoice_en.pdf."""
    if not args:
        default = DATA_DIR / "invoice_en.pdf"
        if default.exists():
            return [default]
        path = make_sample_pdf(Path(__file__).with_name("sample_invoice.pdf"))
        print(f"data/ 폴더가 없어 샘플 PDF를 만들었습니다: {path}")
        return [path]
    pdfs: list[Path] = []
    for arg in args:
        p = Path(arg).expanduser()
        pdfs.extend(sorted(p.glob("*.pdf")) if p.is_dir() else [p])
    return pdfs


# 서버 과부하·요청 한도 같은 '일시적' 오류를 알아보는 패턴 (재시도 후에도 실패했을 때 안내용)
TRANSIENT_ERROR_PATTERN = r"\b(503|529|429|500|502|504)\b|UNAVAILABLE|RESOURCE_EXHAUSTED|overloaded|high demand|rate.?limit|try again later"


def _error_text(e: BaseException) -> str:
    """예외와 그 원인(cause/context)까지 이어 붙인 메시지 — ADK가 원래 오류를 감싸서 올리는 경우 대비."""
    parts, seen = [], set()
    while e is not None and id(e) not in seen:
        seen.add(id(e)); parts.append(f"{type(e).__name__}: {e}")
        e = e.__cause__ or e.__context__
    return " | ".join(parts)


def transient_error_message(e: BaseException, label: str) -> str | None:
    msg = _error_text(e)
    if not re.search(TRANSIENT_ERROR_PATTERN, msg, re.I):
        return None
    short = re.search(r"(\b\d{3}\b[^|]{0,160})", msg)
    return (f"⏳ 모델 서버가 일시적으로 응답하지 못했습니다 ({label})\n"
            f"   {short.group(1).strip() if short else msg[:160]}\n"
            "   자동 재시도(최대 6회)까지 실패했습니다. 이는 코드 문제가 아니라 서버 과부하·요청 한도 때문입니다.\n"
            "   → 1~2분 뒤 다시 실행하거나, 다른 모델을 써 보세요.\n"
            "     예) ADK_MODEL=gemini-3.5-flash-lite python ...   /   ADK_PROVIDER=claude python ...")


def check_api_key() -> None:
    """실행 전에 선택된 모델의 API 키가 있는지 확인하고, 없으면 설정 방법을 안내합니다."""
    provider = "claude" if MODEL_LABEL.startswith("Claude") else "openai" if MODEL_LABEL.startswith("OpenAI") else "gemini"
    if not _has_key(provider) and not (provider == "claude" and "Vertex" in MODEL_LABEL):
        raise SystemExit(
            f"선택된 모델: {MODEL_LABEL}\n"
            "API 키가 설정되어 있지 않습니다. 아래 중 하나를 설정하세요.\n"
            "  export GOOGLE_API_KEY=...      # Gemini\n"
            "  export ANTHROPIC_API_KEY=...   # Claude (Claude Code에서 쓰는 Anthropic API 키)\n"
            "  export OPENAI_API_KEY=...      # OpenAI (Codex에서 쓰는 OpenAI API 키)"
        )


def main() -> None:
    check_api_key()
    print(f"🧠 사용 모델: {MODEL_LABEL}")
    pdfs = collect_pdfs(sys.argv[1:])
    for pdf_path in pdfs:
        print(f"\n{'=' * 70}\n▶ 처리 중: {pdf_path}\n{'=' * 70}")
        try:
            state = asyncio.run(run_pipeline(str(pdf_path.resolve())))
        except Exception as e:  # 키 오류는 긴 추적 대신 짧게 안내
            transient = transient_error_message(e, MODEL_LABEL)
            if transient:
                raise SystemExit(transient)
            msg = f"{type(e).__name__}: {e}"
            if re.search(r"Unauthorized|Authentication|API key|api_key|401|PERMISSION_DENIED|invalid.*key", msg, re.I):
                raise SystemExit(f"❌ API 키 인증 실패 ({MODEL_LABEL})\n   {msg[:200]}\n"
                                 "   키 값이 맞는지, 해당 서비스의 API 키(구독 로그인 아님)인지 확인하세요. README의 '문제 해결' 참고.")
            raise

        print("\n----- session.state['structured_data'] -----\n")
        print(state.get("structured_data", "(없음)"))
        print("\n----- 최종 요약 (session.state['summary']) -----\n")
        print(state.get("summary", "(없음)"))


if __name__ == "__main__":
    main()
