"""
법인 송금 승인 예제 (Google ADK - Human-in-the-Loop 패턴, "안전망")

출처: Google Developers Blog, "Developer's guide to multi-agent patterns in ADK"
      https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/

구조:
    workflow = SequentialAgent([TransactionAgent, ApprovalToolAgent])

    ① TransactionAgent ─ 일상 처리. check_policy로 정책 확인
         ├─ 한도 이내 + 등록 거래처 → process_payment로 바로 송금
         ├─ 잔액 부족 등            → 차단
         └─ 고위험(한도 초과·신규 거래처) → request_approval (= 블로그의 ApprovalTool)
                                          → state["pending_approval"]에 승인 대기 등록
    ② ApprovalToolAgent ─ 대기 중인 거래가 있으면 execute_approved_transaction 호출
         └─ 이 도구는 require_confirmation=True
              → ADK가 실행을 '실제로 멈추고' adk_request_confirmation 이벤트를 보냄
              → 사람이 승인/거절 응답 → 멈춘 자리에서 재개 → 승인이면 송금, 거절이면 취소

    ※ 블로그 의사코드와 다른 점
      - LLM에게 "멈추고 사람에게 물어봐"라고 지시하는 것만으로는 실행이 멈추지 않습니다.
        ADK의 도구 확인(Tool Confirmation, require_confirmation) 기능으로 실제로 멈추게 했습니다.
      - App(resumability_config=ResumabilityConfig(is_resumable=True))로 실행합니다.
        이 설정이 없으면 승인 후 SequentialAgent가 처음부터 다시 돌아 TransactionAgent의
        일상 송금이 '두 번' 처리될 수 있습니다(실험으로 확인, README 참고).
      - ADK는 재개 시 '최소 한 번(at-least-once)' 실행만 보장하므로, 송금 도구는
        같은 요청이 다시 와도 한 번만 처리되도록 멱등(idempotent)하게 만들었습니다.
      - 승인 정책은 프롬프트가 아니라 코드(check_policy, process_payment)에서 강제합니다.
        LLM이 실수로 고액을 process_payment로 보내도 코드가 거부합니다.

설치:
    pip install -U google-adk
    pip install -U anthropic                   # Claude를 쓸 때만
    pip install -U openai                      # OpenAI GPT를 쓸 때만

API 키 (아래 중 하나만 있으면 자동으로 감지해 해당 모델을 사용):
    export GOOGLE_API_KEY=...       # Gemini      — https://aistudio.google.com
    export ANTHROPIC_API_KEY=...    # Claude      — Claude Code에서 쓰는 Anthropic API 키 (pip install anthropic)
    export OPENAI_API_KEY=...       # OpenAI GPT  — Codex에서 쓰는 OpenAI API 키 (pip install openai)
    # 또는 Vertex AI: export GOOGLE_GENAI_USE_VERTEXAI=TRUE GOOGLE_CLOUD_PROJECT=... GOOGLE_CLOUD_LOCATION=...
    키가 여러 개면 ADK_PROVIDER=gemini|claude|openai 로 고르고, 모델은 ADK_MODEL 로 직접 지정할 수 있습니다.

실행: (자세한 사용법은 README.md 참고)
    python adk_human_in_the_loop.py --demo           # 시나리오 5개, 승인 여부는 터미널에서 직접 입력
    python adk_human_in_the_loop.py --demo --auto    # 시나리오의 demo_decision으로 자동 승인/거절
    python adk_human_in_the_loop.py "운영 계좌에서 그린오피스 사무용품에 230,000원 송금해 줘"

모델 지정 예) export ADK_MODEL=gemini-3.5-flash-lite / claude-opus-5-5 / gpt-5.6-luna
"""

import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.apps import App, ResumabilityConfig
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool, ToolContext
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
        return AnthropicLlm(model=name), f"Claude ({name}, Anthropic API 키)", provider
    if provider == "openai":
        try:
            import openai  # noqa: F401
        except ImportError:
            raise SystemExit("OpenAI 모델을 쓰려면 openai 패키지가 필요합니다:  pip install -U openai")
        return name, f"OpenAI ({name}, OpenAI API 키)", provider
    if provider == "claude":
        return name, f"Claude ({name}, Vertex AI)", provider
    return name, f"Gemini ({name})", provider


MODEL, MODEL_LABEL, MODEL_PROVIDER = resolve_model()
_READY = [False]


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
        msg = f"{type(e).__name__}: {e}"
        if _re.search(r"Unauthorized|Authentication|API key|api_key|401|PERMISSION_DENIED|invalid.*key", msg, _re.I):
            raise SystemExit(f"❌ API 키 인증 실패 ({MODEL_LABEL})\n   {msg[:200]}\n"
                             "   키 값이 맞는지, 해당 서비스의 API 키(구독 로그인 아님)인지 확인하세요. README의 '문제 해결' 참고.")
        raise
APP_NAME = "hitl_payment_app"
DATA_DIR = Path(__file__).parent / "data"
CONFIRM_CALL = "adk_request_confirmation"   # ADK가 승인을 요청할 때 쓰는 함수 호출 이름


def _load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


ACCOUNTS = _load("accounts.json")
POLICY = _load("policy.json")


def won(x: int) -> str:
    return f"{x:,}원"


# ---------------------------------------------------------------------------
# 송금 공통 로직 — 잔액과 거래 원장은 세션 상태(session.state)에 보관합니다.
# ---------------------------------------------------------------------------
def _balances(state) -> dict:
    if "balances" not in state:
        state["balances"] = {k: v["balance_krw"] for k, v in ACCOUNTS["accounts"].items()}
    return state["balances"]


def _evaluate(state, from_account: str, payee: str, amount_krw: int) -> dict:
    """정책 판정: blocked(차단) / requires_approval(사람 승인 필요) / auto(자동 처리)."""
    acc = from_account.strip().upper()
    if acc not in ACCOUNTS["accounts"]:
        return {"decision": "blocked", "reasons": [f"존재하지 않는 계좌: {from_account}"]}
    if amount_krw <= 0:
        return {"decision": "blocked", "reasons": ["송금액은 0보다 커야 합니다."]}
    balance = _balances(state)[acc]
    if amount_krw > balance:
        return {"decision": "blocked", "reasons": [f"잔액 부족: 잔액 {won(balance)} < 송금액 {won(amount_krw)}"]}
    reasons = []
    if amount_krw > POLICY["auto_approve_limit_krw"]:
        reasons.append(f"자동 처리 한도({won(POLICY['auto_approve_limit_krw'])}) 초과")
    if POLICY["require_approval_for_new_payee"] and payee.strip() not in ACCOUNTS["registered_payees"]:
        reasons.append(f"미등록(신규) 거래처: {payee}")
    return {"decision": "requires_approval" if reasons else "auto", "reasons": reasons or ["정책 이내"]}


def _transfer(state, from_account: str, payee: str, amount_krw: int, memo: str, approved_by: str | None) -> dict:
    """실제 송금(가상). 같은 거래가 다시 들어와도 한 번만 처리되는 멱등 처리."""
    key = hashlib.sha1(f"{from_account}|{payee}|{amount_krw}|{memo}".encode()).hexdigest()[:10]
    ledger = state.get("ledger", [])
    for row in ledger:
        if row["idempotency_key"] == key:
            return {"status": "already_processed", **row}   # 재개로 다시 호출돼도 이중 송금 없음
    balances = _balances(state)
    acc = from_account.strip().upper()
    balances[acc] -= amount_krw
    row = {"tx_id": f"TX-{datetime.now():%m%d-%H%M%S}-{uuid.uuid4().hex[:4].upper()}", "idempotency_key": key,
           "from": acc, "payee": payee, "amount_krw": amount_krw, "memo": memo,
           "approved_by": approved_by or "자동(정책 이내)", "balance_after": balances[acc]}
    ledger.append(row)
    state["ledger"], state["balances"] = ledger, balances
    return {"status": "success", **row}


# ---------------------------------------------------------------------------
# TransactionAgent의 도구
# ---------------------------------------------------------------------------
def get_account(account_id: str, tool_context: ToolContext) -> dict:
    """계좌 이름과 현재 잔액을 조회합니다.

    Args:
        account_id: 계좌 ID (예: "OPS-001").
    """
    acc = account_id.strip().upper()
    if acc not in ACCOUNTS["accounts"]:
        return {"status": "error", "message": f"없는 계좌입니다. 가능한 계좌: {', '.join(ACCOUNTS['accounts'])}"}
    return {"status": "success", "account_id": acc, "name": ACCOUNTS["accounts"][acc]["name"],
            "balance_krw": _balances(tool_context.state)[acc]}


def check_policy(from_account: str, payee: str, amount_krw: int, tool_context: ToolContext) -> dict:
    """송금 요청이 회사 정책상 자동 처리 가능한지, 사람 승인이 필요한지, 차단인지 판정합니다.

    Args:
        from_account: 출금 계좌 ID.
        payee: 받는 거래처 이름.
        amount_krw: 송금액(원, 정수).
    """
    return _evaluate(tool_context.state, from_account, payee, amount_krw)


def process_payment(from_account: str, payee: str, amount_krw: int, memo: str, tool_context: ToolContext) -> dict:
    """정책 이내(자동 처리 대상)의 일상 송금을 바로 실행합니다. 고위험 거래는 거부됩니다.

    Args:
        from_account: 출금 계좌 ID.
        payee: 받는 거래처 이름.
        amount_krw: 송금액(원, 정수).
        memo: 송금 메모.
    """
    verdict = _evaluate(tool_context.state, from_account, payee, amount_krw)
    if verdict["decision"] != "auto":   # 정책은 코드가 강제: LLM이 실수해도 고위험 거래는 여기서 막힘
        return {"status": "refused", "decision": verdict["decision"], "reasons": verdict["reasons"],
                "message": "자동 처리 대상이 아닙니다. 승인이 필요하면 request_approval을 사용하세요."}
    return _transfer(tool_context.state, from_account, payee, amount_krw, memo, approved_by=None)


def request_approval(from_account: str, payee: str, amount_krw: int, memo: str, tool_context: ToolContext) -> dict:
    """[ApprovalTool] 고위험 송금을 사람 승인 대기열에 올립니다. 송금은 아직 실행되지 않습니다.

    Args:
        from_account: 출금 계좌 ID.
        payee: 받는 거래처 이름.
        amount_krw: 송금액(원, 정수).
        memo: 송금 메모(목적).
    """
    verdict = _evaluate(tool_context.state, from_account, payee, amount_krw)
    if verdict["decision"] == "blocked":
        return {"status": "blocked", "reasons": verdict["reasons"]}
    pending = {"request_id": f"APR-{len(tool_context.state.get('ledger', [])) + 1:03d}",
               "from_account": from_account.strip().upper(), "payee": payee.strip(), "amount_krw": amount_krw,
               "memo": memo, "reasons": verdict["reasons"]}
    tool_context.state["pending_approval"] = pending
    return {"status": "queued", **pending}


# ---------------------------------------------------------------------------
# ApprovalToolAgent의 도구 — require_confirmation=True 로 '실행을 멈추고 사람에게 묻는' 지점
# ---------------------------------------------------------------------------
def execute_approved_transaction(request_id: str, tool_context: ToolContext) -> dict:
    """사람이 승인한 대기 중 송금을 실행합니다. 호출되면 먼저 사람의 승인을 받기 위해 실행이 멈춥니다.

    Args:
        request_id: 승인 대기 요청 ID (예: "APR-001").
    """
    p = tool_context.state.get("pending_approval")
    if not p or p["request_id"] != request_id:
        return {"status": "error", "message": f"대기 중인 승인 요청 {request_id}이(가) 없습니다."}
    reviewer = None
    if tool_context.tool_confirmation and isinstance(tool_context.tool_confirmation.payload, dict):
        reviewer = tool_context.tool_confirmation.payload.get("reviewer")
    result = _transfer(tool_context.state, p["from_account"], p["payee"], p["amount_krw"], p["memo"],
                       approved_by=reviewer or "승인자")
    tool_context.state["pending_approval"] = None
    return result


# ---------------------------------------------------------------------------
# 에이전트
# ---------------------------------------------------------------------------
transaction_agent = LlmAgent(
    name="TransactionAgent",
    model=MODEL,
    description="송금 요청을 접수해 일상 건은 처리하고 고위험 건은 승인 대기열에 올립니다.",
    instruction=(
        "Handle routine processing. If high stakes, call ApprovalTool.\n\n"
        "당신은 법인 송금 담당자입니다. 사용자의 송금 요청 하나를 처리하세요.\n"
        "1. 요청에서 출금 계좌 ID, 받는 거래처 이름, 금액(원, 정수), 목적(memo)을 파악하세요.\n"
        "2. 반드시 check_policy를 먼저 호출하세요.\n"
        "   - decision이 'auto'면 process_payment로 송금하세요.\n"
        "   - decision이 'requires_approval'이면 request_approval(= ApprovalTool)을 호출하세요. 직접 송금하지 마세요.\n"
        "   - decision이 'blocked'면 송금하지 말고 이유를 안내하세요.\n"
        "3. 결과를 한국어 한두 문장으로 보고하세요. 승인 대기면 '승인자 결재를 기다립니다'라고 알리세요.\n"
        "계좌 ID가 불분명하면 get_account로 확인하세요. 금액이나 거래처를 지어내지 마세요."
    ),
    tools=[get_account, check_policy, process_payment, request_approval],
)

approval_agent = LlmAgent(
    name="ApprovalToolAgent",
    model=MODEL,
    description="승인 대기 중인 고위험 거래에 대해 사람의 결정을 받아 실행하거나 취소합니다.",
    instruction=(
        "Pause execution and request human input.\n\n"
        "승인 대기 중인 거래: {pending_approval?}\n\n"
        "- 위 값이 비어 있거나 None이면 아무 도구도 호출하지 말고 '승인이 필요한 거래가 없습니다.'라고만 답하세요.\n"
        "- 대기 중인 거래가 있으면 그 request_id로 execute_approved_transaction을 호출하세요. "
        "이 도구는 사람의 승인을 받을 때까지 실행이 멈춥니다.\n"
        "- 도구 결과가 success면 송금 완료(거래번호, 금액, 승인자, 잔액)를, "
        "거절(rejected) 오류면 '승인자가 거절하여 송금하지 않았습니다'를 한국어로 보고하세요."
    ),
    tools=[FunctionTool(execute_approved_transaction, require_confirmation=True)],
)

workflow = SequentialAgent(name="PaymentWorkflow", sub_agents=[transaction_agent, approval_agent])

# 재개 가능(resumable) 앱: 승인 후 '멈춘 자리'(ApprovalToolAgent)부터 이어서 실행
app = App(name=APP_NAME, root_agent=workflow,
          resumability_config=ResumabilityConfig(is_resumable=True))

root_agent = workflow  # `adk web` / `adk run` 으로 실행할 때 쓰는 이름


# ---------------------------------------------------------------------------
# 실행 — 승인 요청이 오면 터미널에서 사람(또는 --auto 결정)이 응답
# ---------------------------------------------------------------------------
def ask_human(pending: dict | None, hint: str, auto: dict | None) -> dict:
    print("\n  " + "─" * 62)
    print("  ⏸️  실행이 멈췄습니다 — 사람의 승인이 필요합니다 (Human-in-the-Loop)")
    if pending:
        print(f"     요청 ID : {pending['request_id']}")
        print(f"     출금    : {pending['from_account']} ({ACCOUNTS['accounts'][pending['from_account']]['name']})")
        print(f"     받는 곳 : {pending['payee']}")
        print(f"     금액    : {won(pending['amount_krw'])}")
        print(f"     목적    : {pending['memo']}")
        print(f"     승인 사유: {', '.join(pending['reasons'])}")
    print("  " + "─" * 62)
    if auto is not None:
        print(f"  🤖 (--auto) {auto['reviewer']}: {'승인' if auto['confirmed'] else '거절'} — {auto.get('comment', '')}")
        return auto
    try:
        ans = input("  승인하시겠습니까? [y/N]: ").strip().lower()
        reviewer = input("  승인자 이름: ").strip() or "승인자"
        comment = input("  의견(선택): ").strip()
    except EOFError:
        ans, reviewer, comment = "n", "승인자", "입력 없음"
    return {"confirmed": ans in {"y", "yes", "ㅇ", "예", "승인"}, "reviewer": reviewer, "comment": comment}


async def handle_request(runner: InMemoryRunner, text: str, auto_decision: dict | None) -> None:
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id="user")
    message = types.Content(role="user", parts=[types.Part(text=text)])

    while message is not None:
        confirm_call = None
        async for event in runner.run_async(user_id="user", session_id=session.id, new_message=message):
            for call in event.get_function_calls() or []:
                if call.name == CONFIRM_CALL:
                    confirm_call = call                     # ← 여기서 실행이 멈춤
                else:
                    print(f"  🔧 [{event.author}] {call.name}({json.dumps(call.args, ensure_ascii=False)})")
            for resp in event.get_function_responses() or []:
                # 'requires confirmation' 응답은 ADK 내부 신호(승인 대기)라서 화면에 오류처럼 보이지 않게 숨김
                if resp.name != CONFIRM_CALL and "requires confirmation" not in str(resp.response):
                    short = {k: v for k, v in (resp.response or {}).items() if k in ("status", "decision", "reasons", "tx_id", "error", "message")}
                    print(f"     ↳ {short}")
            if event.is_final_response() and event.content and event.content.parts:
                out = "".join(p.text or "" for p in event.content.parts).strip()
                if out:
                    print(f"\n  🤖 {event.author}: {out}")

        if confirm_call is None:
            message = None                                   # 승인 요청 없이 끝남
            continue
        state = (await runner.session_service.get_session(app_name=APP_NAME, user_id="user", session_id=session.id)).state
        hint = confirm_call.args.get("toolConfirmation", {}).get("hint", "")
        decision = ask_human(state.get("pending_approval"), hint, auto_decision)
        print(f"  ▶️  {'승인' if decision['confirmed'] else '거절'} 응답을 보내고, 멈춘 자리에서 재개합니다.")
        # 사람의 결정을 adk_request_confirmation 호출에 대한 FunctionResponse로 돌려보냄
        message = types.Content(role="user", parts=[types.Part(function_response=types.FunctionResponse(
            id=confirm_call.id, name=CONFIRM_CALL,
            response={"confirmed": decision["confirmed"],
                      "payload": {"reviewer": decision["reviewer"], "comment": decision.get("comment", "")}},
        ))])

    final = (await runner.session_service.get_session(app_name=APP_NAME, user_id="user", session_id=session.id)).state
    ledger = final.get("ledger", [])
    print(f"\n  📒 이번 요청으로 처리된 송금: {len(ledger)}건")
    for row in ledger:
        print(f"     {row['tx_id']}  {row['from']} → {row['payee']}  {won(row['amount_krw'])}  "
              f"(승인: {row['approved_by']}, 잔액 {won(row['balance_after'])})")


def main() -> None:
    runner = InMemoryRunner(app=app)
    auto = "--auto" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--demo" in sys.argv:
        for sc in _load("requests.json")["scenarios"]:
            print(f"\n{'=' * 70}\n▶ 시나리오 {sc['id']}: {sc['title']}\n  요청: {sc['request']}\n  기대: {sc['expect']}\n{'=' * 70}")
            run_safe(handle_request(runner, sc["request"], sc["demo_decision"] if auto else None))
    elif args:
        run_safe(handle_request(runner, " ".join(args), None))
    else:
        print(__doc__.split("실행:")[1].split("다른 모델")[0])


if __name__ == "__main__":
    main()
