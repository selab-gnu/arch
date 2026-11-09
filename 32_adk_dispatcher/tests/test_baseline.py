"""안전망 테스트 — 분리 작업 전의 동작을 그대로 고정합니다.

값이 이상해 보여도 고치지 않습니다(예: get_customer의 status가 'success' 대신 계정 상태로 덮어써짐).
분리 후에도 결과가 똑같은지만 확인합니다. 실제 모델 호출은 하지 않습니다(.refactor/manual_check.md 참고).
"""

import asyncio
import inspect
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import adk_coordinator_dispatcher as m

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
KEY_VARS = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI",
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ADK_MODEL", "ADK_PROVIDER")


@pytest.fixture
def no_keys(monkeypatch):
    for v in KEY_VARS:
        monkeypatch.delenv(v, raising=False)


@pytest.fixture
def fresh_ready():
    m._READY[0] = False
    yield
    m._READY[0] = False


# --- 기존 이름이 원래 파일에서 계속 불러와지는지 ---------------------------------
PUBLIC_NAMES = [
    "DEFAULT_MODELS", "_has_key", "_provider_of", "resolve_model", "MODEL", "MODEL_LABEL", "MODEL_PROVIDER",
    "_READY", "TRANSIENT_ERROR_PATTERN", "_error_text", "transient_error_message", "check_api_key", "run_safe",
    "APP_NAME", "DATA_DIR", "_load", "BILLING_DB", "DIAGNOSTICS_KB",
    "get_customer", "list_invoices", "get_invoice", "request_refund",
    "check_service_status", "lookup_error_code", "search_known_issues",
    "billing_specialist", "tech_support", "coordinator", "root_agent", "ask", "run_demo", "run_chat",
]


@pytest.mark.parametrize("name", PUBLIC_NAMES)
def test_name_still_importable(name):
    assert hasattr(m, name)


# --- 모델 선택 ---------------------------------------------------------------
def test_default_models():
    assert m.DEFAULT_MODELS == {"gemini": "gemini-3.8-flash", "claude": "claude-sonnet-5-5", "openai": "gpt-5.6"}


@pytest.mark.parametrize("model,provider", [
    ("claude-opus-5-5", "claude"), ("gpt-5.6", "openai"), ("o4-mini", "openai"), ("gemini-3.8-flash", "gemini"),
])
def test_provider_of(model, provider):
    assert m._provider_of(model) == provider


def test_has_key(no_keys, monkeypatch):
    assert not any(m._has_key(p) for p in ("gemini", "claude", "openai"))
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    assert m._has_key("gemini")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert m._has_key("claude")


def test_resolve_model_default_gemini(no_keys):
    model, label, provider = m.resolve_model()
    assert (type(model).__name__, label, provider) == ("Gemini", "Gemini (gemini-3.8-flash)", "gemini")


def test_resolve_model_claude_on_vertex(no_keys, monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
    monkeypatch.setenv("ADK_PROVIDER", "claude")
    assert m.resolve_model() == ("claude-sonnet-5-5", "Claude (claude-sonnet-5-5, Vertex AI)", "claude")


def test_resolve_model_bad_provider(no_keys, monkeypatch):
    monkeypatch.setenv("ADK_PROVIDER", "nope")
    with pytest.raises(SystemExit):
        m.resolve_model()


# --- 데이터 / 도구 -------------------------------------------------------------
def test_data_loaded():
    assert m.DATA_DIR == DATA
    assert m.BILLING_DB == json.loads((DATA / "billing_db.json").read_text(encoding="utf-8"))
    assert m.DIAGNOSTICS_KB == json.loads((DATA / "diagnostics_kb.json").read_text(encoding="utf-8"))
    assert len(m._load("demo_scenarios.json")["scenarios"]) == 4


SNAPSHOTS = json.loads((HERE / "tool_snapshots.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", SNAPSHOTS, ids=[f"{c['fn']}({c['args'][0]!r})" for c in SNAPSHOTS])
def test_tool_snapshot(case):
    assert getattr(m, case["fn"])(*case["args"]) == case["result"]


def test_request_refund_records_ticket():
    ctx = SimpleNamespace(state={})
    r1 = m.request_refund("inv-2026-1101", 299.0, "중복 청구", ctx)
    r2 = m.request_refund("INV-2026-1101", 10, "test", ctx)
    assert r1["status"] == "success" and r1["eta"] == "영업일 기준 3~5일" and r1["amount"] == 299.0
    assert re.fullmatch(r"RF-\d{8}-001", r1["ticket_id"]) and r2["ticket_id"].endswith("-002")
    assert ctx.state["refund_tickets"][0] == {"ticket_id": r1["ticket_id"], "invoice_id": "INV-2026-1101",
                                              "amount": 299.0, "reason": "중복 청구"}


@pytest.mark.parametrize("invoice,amount", [("INV-0000", 1), ("INV-2026-1101", 0), ("INV-2026-1101", 99999)])
def test_request_refund_errors(invoice, amount):
    ctx = SimpleNamespace(state={})
    assert m.request_refund(invoice, amount, "x", ctx)["status"] == "error"
    assert ctx.state == {}


# --- 에이전트 구성 -------------------------------------------------------------
def test_agent_structure():
    assert m.root_agent is m.coordinator
    assert m.APP_NAME == "support_dispatcher_app"
    assert [a.name for a in m.coordinator.sub_agents] == ["BillingSpecialist", "TechSupportSpecialist"]
    assert [t.__name__ for t in m.billing_specialist.tools] == ["get_customer", "list_invoices", "get_invoice", "request_refund"]
    assert [t.__name__ for t in m.tech_support.tools] == ["check_service_status", "lookup_error_code", "search_known_issues"]
    assert all(a.model is m.MODEL for a in (m.coordinator, m.billing_specialist, m.tech_support))
    assert "CoordinatorAgent" in m.billing_specialist.instruction and "CoordinatorAgent" in m.tech_support.instruction


def test_run_helpers_are_async():
    assert all(inspect.iscoroutinefunction(f) for f in (m.ask, m.run_demo, m.run_chat))


def test_run_chat_quits_without_model_call(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "quit")
    asyncio.run(m.run_chat())
    assert "Acme Cloud 고객 지원입니다" in capsys.readouterr().out


# --- 오류 안내 / 안전 실행 --------------------------------------------------------
def test_error_text_chain():
    try:
        try:
            raise ValueError("inner")
        except ValueError as inner:
            raise RuntimeError("outer") from inner
    except RuntimeError as e:
        assert m._error_text(e) == "RuntimeError: outer | ValueError: inner"


def test_transient_error_message():
    assert m.transient_error_message(RuntimeError("429 RESOURCE_EXHAUSTED"), "L").startswith(
        "⏳ 모델 서버가 일시적으로 응답하지 못했습니다 (L)\n   429 RESOURCE_EXHAUSTED\n")
    assert m.transient_error_message(ValueError("bad"), "L") is None


def test_check_api_key(no_keys, monkeypatch):
    with pytest.raises(SystemExit):
        m.check_api_key()
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert m.check_api_key() is None


async def _ok():
    return 42


async def _boom(msg):
    raise RuntimeError(msg)


def test_run_safe_no_key(no_keys, fresh_ready):
    coro = _ok()
    with pytest.raises(SystemExit):
        m.run_safe(coro)
    assert coro.cr_frame is None  # 시작하지 않은 작업을 닫았는지
    assert m._READY[0] is False


def test_run_safe_ok_prints_model_once(no_keys, fresh_ready, monkeypatch, capsys):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert m.run_safe(_ok()) == 42
    assert m.run_safe(_ok()) == 42
    assert capsys.readouterr().out.count("🧠 사용 모델:") == 1


@pytest.mark.parametrize("msg,expected", [
    ("503 UNAVAILABLE", "⏳ 모델 서버가 일시적으로"),
    ("401 Unauthorized", "❌ API 키 인증 실패"),
])
def test_run_safe_error_messages(no_keys, fresh_ready, monkeypatch, msg, expected):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    with pytest.raises(SystemExit) as exc:
        m.run_safe(_boom(msg))
    assert str(exc.value).startswith(expected)


def test_run_safe_other_errors_propagate(no_keys, fresh_ready, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    with pytest.raises(RuntimeError):
        m.run_safe(_boom("something else"))
