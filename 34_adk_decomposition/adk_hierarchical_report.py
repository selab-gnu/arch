"""
AI 트렌드 보고서 작성 예제 (Google ADK - Hierarchical Decomposition 패턴, "러시아 인형")

출처: Google Developers Blog, "Developer's guide to multi-agent patterns in ADK"
      https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/

구조:
    Level 1  ReportWriter ── 보고서를 계획하고 작성 (직접 조사하지 않음)
               └─ tools: AgentTool(ResearchAssistant)       ← 하위 계층 전체를 '함수 하나'처럼 호출
    Level 2      ResearchAssistant ── 조사 요청 하나를 받아 검색 → 요약 후 결과 반환
                   └─ tools: AgentTool(WebSearchAgent), AgentTool(SummarizerAgent)
    Level 3          WebSearchAgent  ── 웹 검색으로 사실 수집 (search_web 또는 google_search)
                     SummarizerAgent ── 수집한 원문을 핵심 사실로 압축

    ReportWriter → ResearchAssistant → WebSearchAgent → (결과) → ResearchAssistant → SummarizerAgent
                 → (결과) → ResearchAssistant → (조사 결과) → ReportWriter → 보고서

    ※ 블로그 의사코드와 다른 점 — Level 2를 sub_agents 대신 AgentTool로 연결했습니다.
       sub_agents는 '대화 제어권을 넘기는(transfer)' 방식이라, ResearchAssistant가 WebSearchAgent에게
       넘기는 순간 차례가 끝나 버려 SummarizerAgent가 실행되지 않고 검색 원문이 그대로 위로 올라갑니다.
       "위임 → 결과를 기다림 → 이어서 추론"하는 러시아 인형 구조는 AgentTool로만 만들어집니다.
       (README.md의 '왜 Level 2도 AgentTool인가' 참고)

검색 모드:
    기본(local) : data/web_corpus.json 의 '가상 웹' 문서를 검색 — 오프라인, 결과 재현 가능
    --live      : Gemini 내장 google_search 도구로 실제 웹 검색 (Gemini 모델 전용 — Claude/OpenAI는 기본 모드 사용)

설치:
    pip install -U google-adk
    pip install -U anthropic                   # Claude를 쓸 때만
    pip install -U openai                      # OpenAI GPT를 쓸 때만

API 키 (아래 중 하나만 있으면 자동으로 감지해 해당 모델을 사용):
    export GOOGLE_API_KEY=...       # Gemini      — https://aistudio.google.com
    export ANTHROPIC_API_KEY=...    # Claude      — Claude Code에서 쓰는 Anthropic API 키 (pip install anthropic)
    export OPENAI_API_KEY=...       # OpenAI GPT  — Codex에서 쓰는 OpenAI API 키 (pip install openai)
    키가 여러 개면 ADK_PROVIDER=gemini|claude|openai 로 고르고, 모델은 ADK_MODEL 로 직접 지정할 수 있습니다.

실행: (자세한 사용법은 README.md 참고)
    python adk_hierarchical_report.py                                # "2026년 AI 트렌드" 보고서 (가상 웹)
    python adk_hierarchical_report.py "AI 에이전트 보안 위협과 대응"     # 주제 지정
    python adk_hierarchical_report.py "AI 트렌드" --live             # 실제 웹 검색
    python adk_hierarchical_report.py --no-save                      # reports/ 에 저장하지 않음

모델 지정 예) export ADK_MODEL=gemini-3.5-flash-lite / claude-opus-5-5 / gpt-5.6-luna
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

# 실습 화면을 깔끔하게: ADK의 실험 기능 경고와 내부 안내 로그는 숨깁니다 (오류는 그대로 표시).
import logging
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module=r"google\.adk")
warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")          # 실험 기능 안내
warnings.filterwarnings("ignore", message=r".*deprecated in favor of Workflow")  # ADK 2.x 워크플로 에이전트 안내
logging.getLogger("google_adk").setLevel(logging.CRITICAL)  # ADK 내부의 중복 오류 로그 숨김 (예외 자체는 그대로 전달됨)

import re as _re


# ---------------------------------------------------------------------------
# 모델 선택 — 가지고 있는 API 키에 맞춰 Gemini / Claude / OpenAI 중 자동 선택 (model_config.py)
# ---------------------------------------------------------------------------
from model_config import DEFAULT_MODELS, _has_key, _provider_of, resolve_model  # noqa: F401  (기존 import 호환)


MODEL, MODEL_LABEL, MODEL_PROVIDER = resolve_model()
_READY = [False]


# 일시적 오류(서버 과부하·요청 한도) 안내 문구 (error_messages.py)
from error_messages import TRANSIENT_ERROR_PATTERN, _error_text, transient_error_message  # noqa: F401  (기존 import 호환)


def check_api_key() -> None:
    """실행 전에 선택된 모델의 API 키가 있는지 확인하고, 없으면 설정 방법을 안내합니다."""
    if not _has_key(MODEL_PROVIDER) and "Vertex" not in MODEL_LABEL:
        raise SystemExit(
            f"선택된 모델: {MODEL_LABEL}\n"
            "API 키가 설정되어 있지 않습니다. 아래 중 하나를 설정하세요.\n"
            "  export GOOGLE_API_KEY=...      # Gemini\n"
            "  export ANTHROPIC_API_KEY=...   # Claude (Claude Code에서 쓰는 Anthropic API 키)\n"
            "  export OPENAI_API_KEY=...      # OpenAI (Codex에서 쓰는 OpenAI API 키)"
        )


def run_safe(coro):
    """asyncio.run 대신 사용: 처음 한 번 키를 확인해 사용 모델을 알리고, 인증 오류는 짧게 안내합니다."""
    if not _READY[0]:
        try:
            check_api_key()
        except SystemExit:
            coro.close()   # 시작하지 않은 작업을 정리 (경고 방지)
            raise
        print(f"🧠 사용 모델: {MODEL_LABEL}")
        _READY[0] = True
    try:
        return asyncio.run(coro)
    except Exception as e:
        transient = transient_error_message(e, MODEL_LABEL)
        if transient:
            raise SystemExit(transient)
        msg = f"{type(e).__name__}: {e}"
        if _re.search(r"Unauthorized|Authentication|API key|api_key|401|PERMISSION_DENIED|invalid.*key", msg, _re.I):
            raise SystemExit(f"❌ API 키 인증 실패 ({MODEL_LABEL})\n   {msg[:200]}\n"
                             "   키 값이 맞는지, 해당 서비스의 API 키(구독 로그인 아님)인지 확인하세요. README의 '문제 해결' 참고.")
        raise
APP_NAME = "hierarchical_report_app"
BASE_DIR = Path(__file__).parent
REPORT_DIR = BASE_DIR / "reports"
DEFAULT_TOPIC = "2026년 AI 트렌드"


# ---------------------------------------------------------------------------
# Level 3 도구 — 오프라인 '가상 웹' 검색, data/web_corpus.json 사용 (search_tools.py)
# ---------------------------------------------------------------------------
from search_tools import CORPUS_PATH, _load_corpus, search_web  # noqa: F401  (기존 import 호환)


# ---------------------------------------------------------------------------
# 실행 과정을 '들여쓴 트리'로 보여 주는 콜백 (trace_callbacks.py)
#   _T0(시작 시각)은 리스트라서 아래 write_report가 _T0[0]을 바꾸면 콜백 쪽에도 그대로 반영됩니다.
# ---------------------------------------------------------------------------
from trace_callbacks import (  # noqa: F401  (기존 import 호환)
    LEVEL, _T0, _log, on_agent_start, on_agent_end, on_tool_call,
)


# ---------------------------------------------------------------------------
# 에이전트 계층 구성
# ---------------------------------------------------------------------------
def build_report_writer(live: bool = False) -> LlmAgent:
    hooks = dict(before_agent_callback=on_agent_start, after_agent_callback=on_agent_end,
                 before_tool_callback=on_tool_call)

    # ---- Level 3: Tool Agents ----
    web_searcher = LlmAgent(
        name="WebSearchAgent",
        model=MODEL,
        description="Searches web for facts. 조사 요청 하나에 대해 웹을 검색해 출처가 달린 사실을 수집합니다.",
        instruction=(
            "당신은 웹 검색 담당입니다. 요청받은 주제에 대해 검색어를 바꿔 가며 2~3번 검색하세요.\n"
            "검색 결과에 있는 사실만, 출처(제목·매체·날짜·URL)와 함께 빠짐없이 나열하세요. "
            "요약하거나 해석하지 말고, 검색 결과에 없는 내용은 절대 추가하지 마세요."
        ),
        # live 모드는 Gemini 내장 Google 검색, 기본은 오프라인 가상 웹 검색
        tools=[google_search] if live else [search_web],
        **hooks,
    )
    summarizer = LlmAgent(
        name="SummarizerAgent",
        model=MODEL,
        description="Condenses text. 긴 검색 원문을 출처가 달린 핵심 사실 몇 줄로 압축합니다.",
        instruction=(
            "당신은 요약 담당입니다. 받은 원문을 핵심 사실 3~6개의 bullet로 압축하세요.\n"
            "- 숫자·날짜·주체는 원문 그대로 유지하고, 각 bullet 끝에 (매체, 날짜, URL)을 붙이세요.\n"
            "- 서로 다른 출처가 같은 이야기를 하면 하나로 합치고, 원문에 없는 내용은 추가하지 마세요."
        ),
        **hooks,
    )

    # ---- Level 2: Coordinator Agent ----
    research_assistant = LlmAgent(
        name="ResearchAssistant",
        model=MODEL,
        description="Finds and summarizes info. 조사 주제 하나를 받아 검색과 요약을 거친 조사 결과를 돌려줍니다.",
        instruction=(
            "당신은 조사 보조원입니다. 조사 요청 하나를 받으면 다음 순서를 반드시 지키세요.\n"
            "1. WebSearchAgent를 호출해 관련 사실을 수집합니다.\n"
            "2. 수집된 원문 전체를 SummarizerAgent에 넘겨 핵심 사실로 압축합니다.\n"
            "3. 요약된 사실을 출처와 함께 그대로 반환합니다. 직접 지어내지 마세요.\n"
            "검색 결과가 비어 있으면 '관련 자료를 찾지 못함'이라고 반환하세요."
        ),
        # Coordinator manages the tool agents
        # (블로그는 sub_agents=[...]지만, 결과를 돌려받아 다음 단계로 이어 가려면 AgentTool이어야 합니다)
        tools=[AgentTool(agent=web_searcher), AgentTool(agent=summarizer)],
        **hooks,
    )

    # ---- Level 1: Top-Level Agent ----
    return LlmAgent(
        name="ReportWriter",
        model=MODEL,
        description="주제에 대한 종합 보고서를 작성합니다.",
        instruction=(
            "Write a comprehensive report on AI trends. Use the ResearchAssistant to gather info.\n\n"
            "사용자가 준 주제로 한국어 보고서를 작성하세요. 직접 검색하지 말고 다음 순서로 일하세요.\n"
            "1. 주제를 서로 겹치지 않는 하위 주제 3~4개로 나눕니다.\n"
            "2. 하위 주제마다 ResearchAssistant를 한 번씩 호출해 조사 결과를 받습니다.\n"
            "3. 받은 조사 결과만 근거로 마크다운 보고서를 씁니다.\n"
            "   형식: # 제목 / ## 요약(3줄) / ## 하위 주제별 섹션(수치와 출처 포함) / ## 시사점 / ## 출처(URL 목록)\n"
            "조사 결과에 없는 수치나 사실은 쓰지 말고, 자료가 부족한 부분은 '추가 조사 필요'로 표시하세요."
        ),
        # Wrap the sub-agent hierarchy as a tool for the parent
        tools=[AgentTool(agent=research_assistant)],
        **hooks,
    )


SEARCH_MODE = os.environ.get("ADK_SEARCH_MODE", "local")
root_agent = build_report_writer(live=SEARCH_MODE == "live")  # `adk web` / `adk run` 용


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------
async def write_report(topic: str, live: bool) -> str:
    agent = build_report_writer(live=live)
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id="user")
    message = types.Content(role="user", parts=[types.Part(text=f"주제: {topic}")])

    _T0[0] = time.perf_counter()
    report = ""
    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=message):
        if event.author == "ReportWriter" and event.is_final_response() and event.content and event.content.parts:
            report = "".join(p.text or "" for p in event.content.parts).strip()
    return report


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    live = "--live" in sys.argv or SEARCH_MODE == "live"
    topic = " ".join(args) or DEFAULT_TOPIC
    if live and MODEL_PROVIDER != "gemini":
        raise SystemExit(f"--live(실제 웹 검색)는 Gemini 내장 google_search 도구라서 Gemini 모델에서만 동작합니다.\n"
                         f"현재 모델: {MODEL_LABEL}\n"
                         "→ --live 없이 실행하면(가상 웹 검색) 이 모델로도 동작합니다. 또는 ADK_PROVIDER=gemini 로 바꾸세요.")

    print(f"▶ 주제: {topic}")
    print(f"▶ 검색 모드: {'실제 웹 (google_search)' if live else '가상 웹 (data/web_corpus.json)'}\n")
    report = run_safe(write_report(topic, live))

    print(f"\n{'#' * 70}\n📄 최종 보고서 (ReportWriter)\n{'#' * 70}\n\n{report or '(보고서를 받지 못했습니다)'}")
    if report and "--no-save" not in sys.argv:
        REPORT_DIR.mkdir(exist_ok=True)
        out = REPORT_DIR / f"report_{datetime.now():%Y%m%d_%H%M%S}.md"
        out.write_text(report + "\n", encoding="utf-8")
        print(f"\n💾 저장: {out}")


if __name__ == "__main__":
    main()
