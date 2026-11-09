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
    키가 여러 개면 ADK_PROVIDER=gemini|claude|openai 로 고르고, 모델은 ADK_MODEL 로 직접 지정할 수 있습니다.

실행: (자세한 사용법은 README.md 참고)
    python adk_sequential_pipeline.py                         # data/invoice_en.pdf 처리
    python adk_sequential_pipeline.py data/service_contract_ko.pdf
    python adk_sequential_pipeline.py data/                   # data 폴더의 PDF 전체 처리
    python adk_sequential_pipeline.py ~/Documents/my.pdf      # 내 PDF 처리

모델 지정 예) export ADK_MODEL=gemini-3.5-flash-lite / claude-opus-5-5 / gpt-5.6-luna
"""

import atexit
import asyncio
import re
import sys

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
# 모델 선택 — 가지고 있는 API 키에 맞춰 Gemini / Claude / OpenAI 중 자동 선택 (model_config.py)
# ---------------------------------------------------------------------------
from model_config import DEFAULT_MODELS, _has_key, _provider_of, resolve_model  # noqa: F401  (기존 import 호환)


MODEL, MODEL_LABEL = resolve_model()
# 실행기(이벤트 루프)는 하나만 만들어 계속 씁니다. 건마다 asyncio.run()으로 새 루프를 만들면,
# 처음 만든 연결을 재사용하는 OpenAI·Claude 연결 도구가 두 번째 건부터 'Event loop is closed'로 멈춥니다.
_LOOP_RUNNER = asyncio.Runner()
atexit.register(_LOOP_RUNNER.close)
APP_NAME = "pdf_pipeline_app"


# ---------------------------------------------------------------------------
# 도구(Tools) — PDFParser / RegexExtractor / SummaryEngine 구현 (pdf_tools.py)
#   ADK는 일반 파이썬 함수를 도구로 자동 변환합니다. 타입 힌트와 docstring이
#   LLM에게 보이는 '도구 설명서'가 됩니다.
# ---------------------------------------------------------------------------
from pdf_tools import MAX_CHARS, _PATTERNS, pdf_parser, regex_extractor, summary_engine  # noqa: F401  (기존 import 호환)


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
# 처리할 PDF 고르기 / 샘플 PDF 생성 (pdf_inputs.py)
# ---------------------------------------------------------------------------
from pdf_inputs import DATA_DIR, collect_pdfs, make_sample_pdf  # noqa: F401  (기존 import 호환)


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


# 일시적 오류(서버 과부하·요청 한도) 안내 문구 (error_messages.py)
from error_messages import TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message  # noqa: F401  (기존 import 호환)


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
            state = _LOOP_RUNNER.run(run_pipeline(str(pdf_path.resolve())))
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
