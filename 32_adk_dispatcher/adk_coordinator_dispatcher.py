"""
고객 지원 라우팅 예제 (Google ADK - Coordinator/Dispatcher 패턴, "컨시어지")

출처: Google Developers Blog, "Developer's guide to multi-agent patterns in ADK"
      https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/
      블로그의 의사코드(BillingSystemDB / DiagnosticTool)를 data/*.json을 조회하는 실제 도구로 구현했습니다.

구조:
    사용자 → [CoordinatorAgent] ──(transfer_to_agent)──┬→ BillingSpecialist     (청구·결제·환불)
             의도 분석 후 위임                          │     tools: get_customer, list_invoices,
                                                        │            get_invoice, request_refund
                                                        └→ TechSupportSpecialist (장애·오류·버그)
                                                              tools: check_service_status,
                                                                     lookup_error_code, search_known_issues

    - 코디네이터는 직접 답하지 않고, sub_agents의 description을 보고 알맞은 전문가에게 넘깁니다.
    - 넘기는 동작(transfer)은 ADK의 AutoFlow가 transfer_to_agent 도구로 자동 처리합니다.
    - 위임받은 전문가가 이후 대화를 이어받고, 담당이 아닌 질문은 다시 코디네이터로 돌려보냅니다.

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
    python adk_coordinator_dispatcher.py           # 대화형 상담 (종료: quit)
    python adk_coordinator_dispatcher.py --demo    # data/demo_scenarios.json 의 시나리오 자동 실행

모델 지정 예) export ADK_MODEL=gemini-3.5-flash-lite / claude-opus-5-5 / gpt-5.6-luna
"""

import asyncio
import re
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
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
    if _re.match(r"(gpt-|o\d)", model_name):
        return "openai"
    return "gemini"


def resolve_model():
    """ADK에 넘길 모델을 고릅니다. 반환값: (model, 설명 문자열, 공급자)

    - Gemini: 재시도 설정을 넣은 Gemini 객체로 연결합니다.
    - OpenAI: OpenAIResponsesLlm(Responses API)로 연결하며 OPENAI_API_KEY를 사용합니다.
      (문자열 'gpt-...'만 넘기면 Chat Completions 방식으로 연결되어, 추론 모델에서 도구 사용 시 400 오류)
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
        return AnthropicLlm(model=name), f"Claude ({name}, Anthropic API 키)", provider
    if provider == "openai":
        try:
            import openai  # noqa: F401
            from google.adk.integrations.openai import OpenAIResponsesLlm
        except ImportError:
            raise SystemExit("OpenAI 모델을 쓰려면 openai 패키지가 필요합니다:  pip install -U openai")
        # Responses API(/v1/responses)로 연결합니다. gpt-5.x 같은 추론 모델은 예전 Chat Completions 방식에서
        # 도구(function tools)를 함께 쓸 수 없어 400 오류가 납니다. OPENAI_API_KEY는 SDK가 자동으로 읽습니다.
        return OpenAIResponsesLlm(model=name), f"OpenAI ({name}, OpenAI API 키)", provider
    if provider == "claude":
        return name, f"Claude ({name}, Vertex AI)", provider
    # Gemini는 일시적 오류(요청 폭주 503, 한도 429 등)에서 자동으로 재시도하도록 설정합니다.
    from google.adk.models.google_llm import Gemini
    from google.genai import types as _gtypes
    gemini = Gemini(model=name, retry_options=_gtypes.HttpRetryOptions(
        attempts=6, initial_delay=2, max_delay=30, exp_base=2,
        http_status_codes=[408, 429, 500, 502, 503, 504]))
    return gemini, f"Gemini ({name})", provider


MODEL, MODEL_LABEL, MODEL_PROVIDER = resolve_model()
_READY = [False]


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
APP_NAME = "support_dispatcher_app"
DATA_DIR = Path(__file__).with_name("data")


def _load(name: str) -> dict:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


BILLING_DB = _load("billing_db.json")
DIAGNOSTICS_KB = _load("diagnostics_kb.json")


# ---------------------------------------------------------------------------
# 도구 1 — BillingSystemDB (청구 시스템 조회·환불 접수)
#   ADK는 일반 파이썬 함수를 도구로 자동 변환합니다. 타입 힌트와 docstring이
#   LLM에게 보이는 '도구 설명서'가 되므로 정확하게 작성합니다.
# ---------------------------------------------------------------------------
def get_customer(customer_id: str) -> dict:
    """고객 ID로 고객 정보(이름, 요금제, 월 요금, 계정 상태, 결제 수단)를 조회합니다.

    Args:
        customer_id: 고객 ID (예: "C-1001").
    """
    customer = BILLING_DB["customers"].get(customer_id.strip().upper())
    if not customer:
        return {"status": "error", "message": f"고객 {customer_id}을(를) 찾을 수 없습니다."}
    return {"status": "success", "customer_id": customer_id.upper(), **customer}


def list_invoices(customer_id: str) -> dict:
    """고객의 청구서 목록(청구서 번호, 기간, 총액, 결제 상태)을 조회합니다.

    Args:
        customer_id: 고객 ID (예: "C-1001").
    """
    cid = customer_id.strip().upper()
    rows = [
        {"invoice_id": iid, "period": inv["period"], "total": inv["total"], "status": inv["status"], "due": inv["due"]}
        for iid, inv in BILLING_DB["invoices"].items()
        if inv["customer_id"] == cid
    ]
    if not rows:
        return {"status": "error", "message": f"고객 {customer_id}의 청구서가 없습니다."}
    return {"status": "success", "customer_id": cid, "invoices": rows}


def get_invoice(invoice_id: str) -> dict:
    """청구서 한 건의 상세 내역(항목별 금액, 총액, 납부 기한, 결제 상태, 비고)을 조회합니다.

    Args:
        invoice_id: 청구서 번호 (예: "INV-2026-1101").
    """
    inv = BILLING_DB["invoices"].get(invoice_id.strip().upper())
    if not inv:
        return {"status": "error", "message": f"청구서 {invoice_id}을(를) 찾을 수 없습니다."}
    return {"status": "success", "invoice_id": invoice_id.upper(), **inv, "refund_policy": BILLING_DB["refund_policy"]}


def request_refund(invoice_id: str, amount: float, reason: str, tool_context: ToolContext) -> dict:
    """청구서에 대한 환불을 접수하고 접수 번호를 발급합니다. 환불 정책에 맞는 경우에만 호출하세요.

    Args:
        invoice_id: 환불할 청구서 번호.
        amount: 환불 금액 (청구서 통화 기준).
        reason: 환불 사유.
    """
    inv = BILLING_DB["invoices"].get(invoice_id.strip().upper())
    if not inv:
        return {"status": "error", "message": f"청구서 {invoice_id}을(를) 찾을 수 없습니다."}
    if amount <= 0 or amount > inv["total"]:
        return {"status": "error", "message": f"환불 금액은 0보다 크고 청구 총액({inv['total']}) 이하여야 합니다."}

    # 접수 내역은 세션 상태(session.state)에 기록합니다 — 실제 DB 파일은 바꾸지 않습니다.
    tickets = tool_context.state.get("refund_tickets", [])
    ticket_id = f"RF-{datetime.now():%Y%m%d}-{len(tickets) + 1:03d}"
    tickets.append({"ticket_id": ticket_id, "invoice_id": invoice_id.upper(), "amount": amount, "reason": reason})
    tool_context.state["refund_tickets"] = tickets
    return {"status": "success", "ticket_id": ticket_id, "amount": amount, "eta": "영업일 기준 3~5일"}


# ---------------------------------------------------------------------------
# 도구 2 — DiagnosticTool (서비스 상태·오류 코드·알려진 이슈 조회)
# ---------------------------------------------------------------------------
def check_service_status(service: str) -> dict:
    """서비스의 현재 운영 상태와 리전별 공지를 조회합니다.

    Args:
        service: 서비스 이름. compute, storage, database, api_gateway, auth 중 하나. 전체는 "all".
    """
    statuses = DIAGNOSTICS_KB["service_status"]
    key = service.strip().lower()
    if key == "all":
        return {"status": "success", "services": statuses}
    if key not in statuses:
        return {"status": "error", "message": f"알 수 없는 서비스입니다. 가능한 값: {', '.join(statuses)}, all"}
    return {"status": "success", "service": key, **statuses[key]}


def lookup_error_code(code: str) -> dict:
    """오류 코드의 의미, 원인, 해결 방법을 조회합니다.

    Args:
        code: 오류 코드 (예: "E504").
    """
    info = DIAGNOSTICS_KB["error_codes"].get(code.strip().upper())
    if not info:
        return {"status": "error", "message": f"{code}는 등록되지 않은 오류 코드입니다."}
    return {"status": "success", "code": code.upper(), **info}


def search_known_issues(keyword: str) -> dict:
    """알려진 이슈(장애·버그)를 키워드로 검색해 우회 방법과 해결 예정 시각을 알려 줍니다.

    Args:
        keyword: 검색어 (서비스 이름, 오류 코드, 증상 등. 예: "storage", "E504", "업로드").
    """
    kw = keyword.strip().lower()
    hits = [i for i in DIAGNOSTICS_KB["known_issues"] if kw in json.dumps(i, ensure_ascii=False).lower()]
    return {"status": "success", "count": len(hits), "issues": hits}


# ---------------------------------------------------------------------------
# 1) 전문가 에이전트 — description은 코디네이터가 읽는 'API 문서'입니다.
#    무엇을 맡는지 구체적으로, 서로 겹치지 않게 작성해야 라우팅이 정확해집니다.
# ---------------------------------------------------------------------------
billing_specialist = LlmAgent(
    name="BillingSpecialist",
    model=MODEL,
    description="Handles billing inquiries and invoices. (요금·청구서·결제 실패·중복 청구·환불 담당)",
    instruction=(
        "당신은 Acme Cloud의 청구 전문 상담원입니다. 한국어로 친절하고 간결하게 답하세요.\n"
        "- 고객 ID나 청구서 번호가 없으면 먼저 요청하세요.\n"
        "- 금액·날짜·상태는 반드시 도구로 조회한 값만 사용하고 추측하지 마세요.\n"
        "- 환불은 get_invoice로 정책(refund_policy)과 비고(note)를 확인한 뒤, 정책에 맞을 때만 request_refund를 호출하세요.\n"
        "- 기술 장애·오류 코드·버그 문의처럼 청구와 무관한 질문이면 직접 답하지 말고 CoordinatorAgent에게 넘기세요."
    ),
    tools=[get_customer, list_invoices, get_invoice, request_refund],
)

tech_support = LlmAgent(
    name="TechSupportSpecialist",
    model=MODEL,
    description="Troubleshoots technical issues. (서비스 장애·오류 코드·버그·연결/업로드 문제 담당)",
    instruction=(
        "당신은 Acme Cloud의 기술 지원 엔지니어입니다. 한국어로 답하세요.\n"
        "- 오류 코드가 있으면 lookup_error_code로, 증상이 있으면 search_known_issues로 확인하세요.\n"
        "- 관련 서비스는 check_service_status로 현재 장애 여부를 꼭 확인하세요.\n"
        "- 답변 형식: 원인 → 지금 해 볼 조치(번호 목록) → 알려진 이슈와 해결 예정 시각(있으면).\n"
        "- 요금·청구·환불 질문이면 직접 답하지 말고 CoordinatorAgent에게 넘기세요."
    ),
    tools=[check_service_status, lookup_error_code, search_known_issues],
)

# ---------------------------------------------------------------------------
# 2) 코디네이터(디스패처) — 의도를 분석해 알맞은 전문가에게 위임
#    sub_agents를 지정하면 ADK가 transfer_to_agent 도구를 자동으로 붙여 줍니다.
# ---------------------------------------------------------------------------
coordinator = LlmAgent(
    name="CoordinatorAgent",
    model=MODEL,
    description="고객 문의의 의도를 분석해 알맞은 전문가에게 연결하는 접수 담당.",
    # The instructions guide the routing logic
    instruction=(
        "Analyze user intent. Route billing issues to BillingSpecialist and bugs to TechSupportSpecialist.\n\n"
        "- 요금, 청구서, 결제, 환불, 요금제 → BillingSpecialist\n"
        "- 장애, 오류 코드, 버그, 느림, 연결·업로드 실패 → TechSupportSpecialist\n"
        "- 직접 답을 만들지 말고 transfer_to_agent로 바로 넘기세요.\n"
        "- 인사만 하거나 의도가 불분명하면, 청구 문의인지 기술 문의인지 한 문장으로만 되물으세요."
    ),
    sub_agents=[billing_specialist, tech_support],
)

root_agent = coordinator  # `adk web` / `adk run` 으로 실행할 때 쓰는 이름


# ---------------------------------------------------------------------------
# 실행 도우미
# ---------------------------------------------------------------------------
async def ask(runner: InMemoryRunner, session_id: str, text: str) -> None:
    """한 턴을 실행하며, 누가 누구에게 넘겼고 어떤 도구를 썼는지 출력합니다."""
    message = types.Content(role="user", parts=[types.Part(text=text)])
    async for event in runner.run_async(user_id="user", session_id=session_id, new_message=message):
        for call in event.get_function_calls() or []:
            if call.name == "transfer_to_agent":
                print(f"   ↪ [{event.author}] → {call.args.get('agent_name')} 에게 위임")
            else:
                print(f"   🔧 [{event.author}] 도구 호출: {call.name}({json.dumps(call.args, ensure_ascii=False)})")
        if event.is_final_response() and event.content and event.content.parts:
            text_out = "".join(p.text or "" for p in event.content.parts).strip()
            if text_out:
                print(f"\n🤖 {event.author}:\n{text_out}\n")


async def run_demo() -> None:
    scenarios = _load("demo_scenarios.json")["scenarios"]
    runner = InMemoryRunner(agent=coordinator, app_name=APP_NAME)
    for sc in scenarios:
        print(f"\n{'=' * 70}\n▶ 시나리오: {sc['title']}\n  ({sc['expect']})\n{'=' * 70}")
        session = await runner.session_service.create_session(app_name=APP_NAME, user_id="user")
        for turn in sc["turns"]:
            print(f"\n🙋 사용자: {turn}")
            await ask(runner, session.id, turn)
        final = await runner.session_service.get_session(app_name=APP_NAME, user_id="user", session_id=session.id)
        if final.state.get("refund_tickets"):
            print(f"📋 session.state['refund_tickets'] = {final.state['refund_tickets']}")


async def run_chat() -> None:
    runner = InMemoryRunner(agent=coordinator, app_name=APP_NAME)
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id="user")
    print("Acme Cloud 고객 지원입니다. 무엇을 도와드릴까요? (종료: quit)")
    print("예) 고객 ID C-1001인데 이번 달 청구서 금액이 이상해요 / 서울 리전에서 업로드하면 E504가 떠요\n")
    while True:
        try:
            text = input("🙋 사용자: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in {"quit", "exit", "q", "종료"}:
            break
        if text:
            await ask(runner, session.id, text)


if __name__ == "__main__":
    run_safe(run_demo() if "--demo" in sys.argv else run_chat())
