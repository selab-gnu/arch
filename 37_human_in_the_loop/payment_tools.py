"""송금 업무 기능 — 계좌·정책 데이터, 정책 판정, 멱등 송금, 에이전트가 쓰는 도구

- 잔액과 거래 원장은 세션 상태(session.state)에 보관합니다. data/*.json 파일은 바뀌지 않습니다.
- 승인 정책은 프롬프트가 아니라 이 파일의 코드(_evaluate, process_payment)에서 강제합니다.
- execute_approved_transaction 은 함수 본문만 여기에 있고, '사람이 승인해야 실행'되도록
  FunctionTool(..., require_confirmation=True)로 감싸는 부분은 adk_human_in_the_loop.py 에 있습니다.
"""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path

from google.adk.tools import ToolContext

DATA_DIR = Path(__file__).parent / "data"


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
