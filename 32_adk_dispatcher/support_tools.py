"""상담 도구(Tools) — 블로그의 BillingSystemDB / DiagnosticTool 을 data/*.json 조회로 구현

ADK는 일반 파이썬 함수를 도구로 자동 변환합니다. 타입 힌트와 docstring이
LLM에게 보이는 '도구 설명서'가 되므로 정확하게 작성합니다.
"""

import json
from datetime import datetime
from pathlib import Path

from google.adk.tools import ToolContext

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
