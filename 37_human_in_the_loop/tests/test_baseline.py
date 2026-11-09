"""안전망 테스트 — 분리 작업 전의 동작을 그대로 고정합니다.

값이 이상해 보여도 고치지 않습니다. 분리 후에도 결과가 똑같은지만 확인합니다.
실제 모델 호출은 하지 않습니다. 승인 흐름(handle_request)은 가짜 러너로 확인합니다(.refactor/manual_check.md 참고).
"""

import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import adk_human_in_the_loop as m

ROOT = Path(__file__).resolve().parent.parent
KEY_VARS = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI",
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ADK_MODEL", "ADK_PROVIDER")


def ctx(state=None, confirmation=None):
    return SimpleNamespace(state={} if state is None else state, tool_confirmation=confirmation)


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
    "APP_NAME", "DATA_DIR", "CONFIRM_CALL", "_load", "ACCOUNTS", "POLICY", "won",
    "_balances", "_evaluate", "_transfer", "get_account", "check_policy", "process_payment", "request_approval",
    "execute_approved_transaction", "transaction_agent", "approval_agent", "workflow", "app", "root_agent",
    "ask_human", "handle_request", "main",
]


@pytest.mark.parametrize("name", PUBLIC_NAMES)
def test_name_still_importable(name):
    assert hasattr(m, name)


# --- 모델 선택 ---------------------------------------------------------------
def test_default_models():
    assert m.DEFAULT_MODELS == {"gemini": "gemini-3.8-flash", "claude": "claude-sonnet-5-5", "openai": "gpt-5.6"}


@pytest.mark.parametrize("model,provider", [("claude-x", "claude"), ("gpt-5.6", "openai"), ("o3", "openai"), ("g", "gemini")])
def test_provider_of(model, provider):
    assert m._provider_of(model) == provider


def test_resolve_model_default_gemini(no_keys):
    model, label, provider = m.resolve_model()
    assert (type(model).__name__, label, provider) == ("Gemini", "Gemini (gemini-3.8-flash)", "gemini")


def test_resolve_model_bad_provider(no_keys, monkeypatch):
    monkeypatch.setenv("ADK_PROVIDER", "nope")
    with pytest.raises(SystemExit):
        m.resolve_model()


# --- 데이터 / 상수 ---------------------------------------------------------------
def test_data_and_constants():
    assert m.APP_NAME == "hitl_payment_app"
    assert m.DATA_DIR == ROOT / "data"
    assert m.CONFIRM_CALL == "adk_request_confirmation"
    assert m.ACCOUNTS == json.loads((ROOT / "data" / "accounts.json").read_text(encoding="utf-8"))
    assert m.POLICY == json.loads((ROOT / "data" / "policy.json").read_text(encoding="utf-8"))
    assert len(m._load("requests.json")["scenarios"]) == 5


@pytest.mark.parametrize("x,expected", [(0, "0원"), (850000, "850,000원"), (12_000_000, "12,000,000원")])
def test_won(x, expected):
    assert m.won(x) == expected


# --- 송금 공통 로직 ---------------------------------------------------------------
def test_balances_initialized_once():
    state = {}
    b = m._balances(state)
    assert b == {"OPS-001": 48_000_000, "PAY-002": 120_000_000, "RND-003": 3_000_000}
    b["OPS-001"] = 1
    assert m._balances(state)["OPS-001"] == 1           # 이미 있으면 그대로 사용
    assert m.ACCOUNTS["accounts"]["OPS-001"]["balance_krw"] == 48_000_000  # 원본 데이터는 바뀌지 않음


@pytest.mark.parametrize("acc,payee,amount,expected", [
    ("OPS-001", "클라우드나인 호스팅", 850_000, {"decision": "auto", "reasons": ["정책 이내"]}),
    (" ops-001 ", "클라우드나인 호스팅", 1_000_000, {"decision": "auto", "reasons": ["정책 이내"]}),
    ("OPS-001", "한빛 소프트웨어 라이선스", 12_000_000,
     {"decision": "requires_approval", "reasons": ["자동 처리 한도(1,000,000원) 초과"]}),
    ("RND-003", "데이터랩스", 300_000, {"decision": "requires_approval", "reasons": ["미등록(신규) 거래처: 데이터랩스"]}),
    ("OPS-001", "퀵마켓 컨설팅", 18_500_000, {"decision": "requires_approval",
     "reasons": ["자동 처리 한도(1,000,000원) 초과", "미등록(신규) 거래처: 퀵마켓 컨설팅"]}),
    ("RND-003", "진주 시설관리", 5_000_000,
     {"decision": "blocked", "reasons": ["잔액 부족: 잔액 3,000,000원 < 송금액 5,000,000원"]}),
    ("XXX-999", "진주 시설관리", 1, {"decision": "blocked", "reasons": ["존재하지 않는 계좌: XXX-999"]}),
    ("OPS-001", "진주 시설관리", 0, {"decision": "blocked", "reasons": ["송금액은 0보다 커야 합니다."]}),
])
def test_evaluate(acc, payee, amount, expected):
    assert m._evaluate({}, acc, payee, amount) == expected


TX_ID = re.compile(r"^TX-\d{4}-\d{6}-[0-9A-F]{4}$")


def test_transfer_is_idempotent():
    state = {}
    r1 = m._transfer(state, "ops-001", "진주 시설관리", 500_000, "보수", approved_by=None)
    r2 = m._transfer(state, "ops-001", "진주 시설관리", 500_000, "보수", approved_by="누구든")
    assert r1["status"] == "success" and TX_ID.match(r1["tx_id"])
    assert {k: v for k, v in r1.items() if k not in ("status", "tx_id")} == {
        "idempotency_key": "f2d4e5f1d1"[:0] + r1["idempotency_key"], "from": "OPS-001", "payee": "진주 시설관리",
        "amount_krw": 500_000, "memo": "보수", "approved_by": "자동(정책 이내)", "balance_after": 47_500_000}
    assert len(r1["idempotency_key"]) == 10
    assert r2 == {**r1, "status": "already_processed"}     # 같은 송금은 한 번만
    assert state["balances"]["OPS-001"] == 47_500_000 and len(state["ledger"]) == 1


def test_transfer_key_uses_raw_account_text():
    state = {}
    m._transfer(state, "OPS-001", "A", 1, "m", None)
    m._transfer(state, "ops-001", "A", 1, "m", None)        # 대소문자가 다르면 다른 멱등 키(현재 동작 그대로 고정)
    assert len(state["ledger"]) == 2 and state["balances"]["OPS-001"] == 48_000_000 - 2


# --- TransactionAgent 도구 --------------------------------------------------------
def test_get_account():
    assert m.get_account(" rnd-003", ctx()) == {"status": "success", "account_id": "RND-003",
                                                 "name": "연구개발 계좌", "balance_krw": 3_000_000}
    assert m.get_account("NOPE", ctx()) == {"status": "error",
                                            "message": "없는 계좌입니다. 가능한 계좌: OPS-001, PAY-002, RND-003"}


def test_check_policy_matches_evaluate():
    assert m.check_policy("OPS-001", "퀵마켓 컨설팅", 18_500_000, ctx()) == m._evaluate({}, "OPS-001", "퀵마켓 컨설팅", 18_500_000)


def test_process_payment_auto_and_refused():
    c = ctx()
    ok = m.process_payment("OPS-001", "클라우드나인 호스팅", 850_000, "11월 서버", c)
    assert ok["status"] == "success" and ok["balance_after"] == 47_150_000
    refused = m.process_payment("OPS-001", "한빛 소프트웨어 라이선스", 12_000_000, "라이선스", c)
    assert refused == {"status": "refused", "decision": "requires_approval",
                       "reasons": ["자동 처리 한도(1,000,000원) 초과"],
                       "message": "자동 처리 대상이 아닙니다. 승인이 필요하면 request_approval을 사용하세요."}
    assert len(c.state["ledger"]) == 1


def test_request_approval_queues_and_blocks():
    c = ctx()
    q = m.request_approval(" ops-001", " 퀵마켓 컨설팅 ", 18_500_000, "선급금", c)
    assert q == {"status": "queued", "request_id": "APR-001", "from_account": "OPS-001", "payee": "퀵마켓 컨설팅",
                 "amount_krw": 18_500_000, "memo": "선급금",
                 # 등록 여부는 공백을 지우고 비교하지만, 사유 문구에는 입력한 거래처 이름이 공백까지 그대로 들어감(현재 동작 고정)
                 "reasons": ["자동 처리 한도(1,000,000원) 초과", "미등록(신규) 거래처:  퀵마켓 컨설팅 "]}
    assert c.state["pending_approval"] == {k: v for k, v in q.items() if k != "status"}
    blocked = m.request_approval("RND-003", "진주 시설관리", 5_000_000, "보수", ctx())
    assert blocked == {"status": "blocked", "reasons": ["잔액 부족: 잔액 3,000,000원 < 송금액 5,000,000원"]}


def test_request_approval_id_counts_ledger():
    c = ctx()
    m.process_payment("OPS-001", "진주 시설관리", 10, "x", c)
    assert m.request_approval("OPS-001", "새 거래처", 10, "y", c)["request_id"] == "APR-002"


# --- ApprovalToolAgent 도구 -------------------------------------------------------
def _queued_ctx(confirmation=None):
    c = ctx(confirmation=confirmation)
    m.request_approval("OPS-001", "한빛 소프트웨어 라이선스", 12_000_000, "연간 라이선스", c)
    return c


def test_execute_approved_transaction_with_reviewer():
    c = _queued_ctx(SimpleNamespace(payload={"reviewer": "이선아 팀장", "comment": "ok"}))
    r = m.execute_approved_transaction("APR-001", c)
    assert r["status"] == "success" and r["approved_by"] == "이선아 팀장" and r["balance_after"] == 36_000_000
    assert c.state["pending_approval"] is None


@pytest.mark.parametrize("confirmation", [None, SimpleNamespace(payload=None), SimpleNamespace(payload="text")])
def test_execute_approved_transaction_default_reviewer(confirmation):
    r = m.execute_approved_transaction("APR-001", _queued_ctx(confirmation))
    assert r["approved_by"] == "승인자"


@pytest.mark.parametrize("state,req", [({}, "APR-001"), ({"pending_approval": None}, "APR-001")])
def test_execute_approved_transaction_nothing_pending(state, req):
    assert m.execute_approved_transaction(req, ctx(state)) == {
        "status": "error", "message": "대기 중인 승인 요청 APR-001이(가) 없습니다."}


def test_execute_approved_transaction_wrong_id():
    c = _queued_ctx()
    assert m.execute_approved_transaction("APR-999", c)["status"] == "error"
    assert c.state["pending_approval"]["request_id"] == "APR-001"


# --- 에이전트 / 앱 구성 -----------------------------------------------------------
def test_agent_structure():
    assert m.root_agent is m.workflow
    assert [a.name for a in m.workflow.sub_agents] == ["TransactionAgent", "ApprovalToolAgent"]
    assert [t.__name__ for t in m.transaction_agent.tools] == ["get_account", "check_policy", "process_payment", "request_approval"]
    tool = m.approval_agent.tools[0]
    assert type(tool).__name__ == "FunctionTool" and tool.func is m.execute_approved_transaction
    assert tool._require_confirmation is True
    assert "{pending_approval?}" in m.approval_agent.instruction
    assert m.app.name == m.APP_NAME and m.app.root_agent is m.workflow
    assert m.app.resumability_config.is_resumable is True
    assert m.transaction_agent.model is m.MODEL and m.approval_agent.model is m.MODEL


# --- 사람에게 묻기 ---------------------------------------------------------------
PENDING = {"request_id": "APR-001", "from_account": "OPS-001", "payee": "퀵마켓 컨설팅", "amount_krw": 18_500_000,
           "memo": "선급금", "reasons": ["자동 처리 한도(1,000,000원) 초과", "미등록(신규) 거래처: 퀵마켓 컨설팅"]}


def test_ask_human_auto(capsys):
    auto = {"confirmed": False, "reviewer": "이선아 팀장", "comment": "계약서 없음"}
    assert m.ask_human(PENDING, "hint", auto) is auto
    out = capsys.readouterr().out
    assert "⏸️  실행이 멈췄습니다 — 사람의 승인이 필요합니다 (Human-in-the-Loop)" in out
    assert "출금    : OPS-001 (운영 계좌)" in out and "금액    : 18,500,000원" in out
    assert "승인 사유: 자동 처리 한도(1,000,000원) 초과, 미등록(신규) 거래처: 퀵마켓 컨설팅" in out
    assert "🤖 (--auto) 이선아 팀장: 거절 — 계약서 없음" in out


@pytest.mark.parametrize("answers,expected", [
    (["y", "김민수", "좋음"], {"confirmed": True, "reviewer": "김민수", "comment": "좋음"}),
    (["승인", "", ""], {"confirmed": True, "reviewer": "승인자", "comment": ""}),
    (["n", "박", "x"], {"confirmed": False, "reviewer": "박", "comment": "x"}),
    ([], {"confirmed": False, "reviewer": "승인자", "comment": "입력 없음"}),   # 입력 끝(EOF)
])
def test_ask_human_input(monkeypatch, capsys, answers, expected):
    it = iter(answers)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)
    assert m.ask_human(None, "", None) == expected
    assert "요청 ID" not in capsys.readouterr().out   # 대기 정보가 없으면 상세를 출력하지 않음


# --- 승인 흐름(handle_request) — 가짜 러너로 '멈춤 → 사람 응답 → 재개'를 확인 ---------------
class FakeEvent:
    def __init__(self, author, calls=(), responses=(), text=None):
        self.author, self._calls, self._responses = author, list(calls), list(responses)
        self.content = SimpleNamespace(parts=[SimpleNamespace(text=text)]) if text else None

    def get_function_calls(self):
        return self._calls

    def get_function_responses(self):
        return self._responses

    def is_final_response(self):
        return self.content is not None


class FakeRunner:
    def __init__(self, pause):
        self.pause, self.messages, self.state = pause, [], {}
        self.session_service = SimpleNamespace(create_session=self._create, get_session=self._get)

    async def _create(self, **kw):
        return SimpleNamespace(id="s1")

    async def _get(self, **kw):
        return SimpleNamespace(state=self.state)

    async def run_async(self, user_id, session_id, new_message):
        self.messages.append(new_message)
        call = lambda name, args, id="c1": SimpleNamespace(name=name, args=args, id=id)  # noqa: E731
        resp = lambda name, response: SimpleNamespace(name=name, response=response)  # noqa: E731
        if len(self.messages) == 1:
            yield FakeEvent("TransactionAgent", calls=[call("check_policy", {"amount_krw": 18500000})])
            yield FakeEvent("TransactionAgent", responses=[resp("check_policy", {"decision": "requires_approval",
                                                                                  "reasons": ["r"], "extra": 1})])
            if self.pause:
                self.state["pending_approval"] = dict(PENDING)
                yield FakeEvent("ApprovalToolAgent", calls=[call("execute_approved_transaction", {"request_id": "APR-001"}),
                                                            call(m.CONFIRM_CALL, {"toolConfirmation": {"hint": "h"}}, id="conf-9")])
                yield FakeEvent("ApprovalToolAgent", responses=[resp("execute_approved_transaction",
                                                                     {"error": "This tool call requires confirmation"})])
            else:
                yield FakeEvent("TransactionAgent", text="정책 이내라 바로 송금했습니다.")
        else:
            self.state["ledger"] = [{"tx_id": "TX-1", "from": "OPS-001", "payee": "퀵마켓 컨설팅", "amount_krw": 18_500_000,
                                     "approved_by": "이선아 팀장", "balance_after": 29_500_000}]
            yield FakeEvent("ApprovalToolAgent", text="송금 완료")


def test_handle_request_pause_and_resume(capsys):
    runner = FakeRunner(pause=True)
    decision = {"confirmed": True, "reviewer": "이선아 팀장", "comment": "확인"}
    asyncio.run(m.handle_request(runner, "보내 줘", decision))
    assert len(runner.messages) == 2                          # 멈췄다가 사람 응답으로 한 번 더 실행
    assert runner.messages[0].parts[0].text == "보내 줘"
    fr = runner.messages[1].parts[0].function_response
    assert (fr.id, fr.name) == ("conf-9", m.CONFIRM_CALL)
    assert fr.response == {"confirmed": True, "payload": {"reviewer": "이선아 팀장", "comment": "확인"}}
    out = capsys.readouterr().out
    assert '🔧 [TransactionAgent] check_policy({"amount_krw": 18500000})' in out
    assert "↳ {'decision': 'requires_approval', 'reasons': ['r']}" in out     # 일부 키만 보여 줌
    assert "requires confirmation" not in out                                # 내부 신호는 숨김
    assert m.CONFIRM_CALL not in out
    assert "⏸️  실행이 멈췄습니다" in out and "▶️  승인 응답을 보내고, 멈춘 자리에서 재개합니다." in out
    assert "🤖 ApprovalToolAgent: 송금 완료" in out
    assert "📒 이번 요청으로 처리된 송금: 1건" in out
    assert "TX-1  OPS-001 → 퀵마켓 컨설팅  18,500,000원  (승인: 이선아 팀장, 잔액 29,500,000원)" in out


def test_handle_request_without_pause(capsys):
    runner = FakeRunner(pause=False)
    asyncio.run(m.handle_request(runner, "소액", None))
    assert len(runner.messages) == 1
    out = capsys.readouterr().out
    assert "⏸️" not in out and "🤖 TransactionAgent: 정책 이내라 바로 송금했습니다." in out
    assert "📒 이번 요청으로 처리된 송금: 0건" in out


# --- main ----------------------------------------------------------------------
def _capture_run_safe(calls):
    def run(coro):
        f = coro.cr_frame.f_locals
        calls.append((f["text"], f["auto_decision"]))
        coro.close()
    return run


def test_main_without_args_prints_usage(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["x.py"])
    m.main()
    out = capsys.readouterr().out
    # 독스트링의 '실행:' 뒤부터 출력. 끝 표시로 찾는 '다른 모델'이 독스트링에 없어서 '모델 지정 예' 줄까지 나옴(현재 동작 고정)
    assert out.startswith(" (자세한 사용법은 README.md 참고)\n")
    assert "--demo --auto" in out and "모델 지정 예)" in out


@pytest.mark.parametrize("auto", [False, True])
def test_main_demo(monkeypatch, capsys, auto):
    calls = []
    monkeypatch.setattr(m, "run_safe", _capture_run_safe(calls))
    monkeypatch.setattr("sys.argv", ["x.py", "--demo"] + (["--auto"] if auto else []))
    m.main()
    scenarios = m._load("requests.json")["scenarios"]
    assert calls == [(s["request"], s["demo_decision"] if auto else None) for s in scenarios]
    assert capsys.readouterr().out.count("▶ 시나리오 ") == 5


def test_main_free_text(monkeypatch):
    calls = []
    monkeypatch.setattr(m, "run_safe", _capture_run_safe(calls))
    monkeypatch.setattr("sys.argv", ["x.py", "운영", "계좌에서", "송금"])
    m.main()
    assert calls == [("운영 계좌에서 송금", None)]


# --- 오류 안내 / 안전 실행 --------------------------------------------------------
def test_transient_error_message():
    assert m.transient_error_message(RuntimeError("503 UNAVAILABLE"), "L").startswith(
        "⏳ 모델 서버가 일시적으로 응답하지 못했습니다 (L)\n   503 UNAVAILABLE\n")
    assert m.transient_error_message(ValueError("bad"), "L") is None


def test_check_api_key(no_keys, monkeypatch):
    with pytest.raises(SystemExit):
        m.check_api_key()
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert m.check_api_key() is None


async def _ok():
    return 1


async def _boom(msg):
    raise RuntimeError(msg)


def test_run_safe_no_key(no_keys, fresh_ready):
    coro = _ok()
    with pytest.raises(SystemExit):
        m.run_safe(coro)
    assert coro.cr_frame is None


def test_run_safe_ok_once(no_keys, fresh_ready, monkeypatch, capsys):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert m.run_safe(_ok()) == 1 and m.run_safe(_ok()) == 1
    assert capsys.readouterr().out.count("🧠 사용 모델:") == 1


@pytest.mark.parametrize("msg,expected", [("429 rate limit", "⏳"), ("Authentication failed", "❌ API 키 인증 실패")])
def test_run_safe_errors(no_keys, fresh_ready, monkeypatch, msg, expected):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    with pytest.raises(SystemExit) as exc:
        m.run_safe(_boom(msg))
    assert str(exc.value).startswith(expected)
