"""안전망 테스트 — 분리 작업 전의 동작을 그대로 고정합니다.

값이 이상해 보여도 고치지 않습니다. 분리 후에도 결과가 똑같은지만 확인합니다.
실제 모델 호출은 하지 않습니다(.refactor/manual_check.md 참고).
"""

import asyncio
import hashlib
import inspect
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import adk_generator_critic as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = json.loads((HERE / "sql_snapshots.json").read_text(encoding="utf-8"))
KEY_VARS = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI",
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ADK_MODEL", "ADK_PROVIDER")


def as_json(value):
    """튜플을 리스트로 바꿔 스냅샷(JSON)과 비교할 수 있게 합니다."""
    return json.loads(json.dumps(value, ensure_ascii=False))


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
    "APP_NAME", "BASE_DIR", "SCHEMA_PATH", "QUESTIONS_PATH", "MAX_ITERATIONS", "SCHEMA_SQL",
    "new_db", "schema_for_prompt", "clean_sql", "validate_sql", "ExitConditionChecker",
    "generator", "critic", "loop", "root_agent", "load_questions", "solve", "run_sql", "same_result", "show", "main",
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


# --- 경로 / 상수 ---------------------------------------------------------------
def test_paths_and_constants():
    assert m.APP_NAME == "sql_generator_critic_app"
    assert m.BASE_DIR == ROOT
    assert m.SCHEMA_PATH == ROOT / "data" / "shop_schema.sql"
    assert m.QUESTIONS_PATH == ROOT / "data" / "questions.json"
    assert m.MAX_ITERATIONS == 5
    assert m.SCHEMA_SQL == m.SCHEMA_PATH.read_text(encoding="utf-8")


# --- 데이터베이스 / SQL 도구 ------------------------------------------------------
def test_new_db_is_fresh_in_memory():
    con = m.new_db()
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.execute("DELETE FROM customers")
    con.close()
    assert {"customers", "products", "orders", "order_items"} <= tables
    con2 = m.new_db()
    assert con2.execute("SELECT COUNT(*) FROM customers").fetchone()[0] > 0  # 매번 새로 만들어짐
    con2.close()


def test_schema_for_prompt():
    text = m.schema_for_prompt()
    assert hashlib.sha256(text.encode()).hexdigest() == SNAP["schema_for_prompt_sha"]
    assert len(text.splitlines()) == SNAP["schema_for_prompt_lines"]
    assert "INSERT" not in text and "CREATE TABLE" in text


@pytest.mark.parametrize("text,expected", [
    ("SELECT 1;", "SELECT 1"),
    ("```sql\nSELECT 1;\n```", "SELECT 1"),
    ("설명\n```SQL\n  SELECT a\n  FROM b ;  \n```\n끝", "SELECT a\n  FROM b"),
    ("```\nSELECT 2\n```", "SELECT 2"),
    ("  plain  ", "plain"),
    ("", ""),
])
def test_clean_sql(text, expected):
    assert m.clean_sql(text) == expected


@pytest.mark.parametrize("case", SNAP["validate_sql"], ids=[c["draft"][:30] or "(empty)" for c in SNAP["validate_sql"]])
def test_validate_sql_snapshot(case):
    assert as_json(m.validate_sql(SimpleNamespace(state={"draft": case["draft"]}))) == case["result"]


def test_validate_sql_missing_draft():
    assert m.validate_sql(SimpleNamespace(state={})) == {"ok": False, "error": "초안 SQL이 비어 있습니다."}


@pytest.mark.parametrize("case", SNAP["run_sql"], ids=[f"q{i + 1}" for i in range(len(SNAP["run_sql"]))])
def test_run_sql_snapshot(case):
    cols, rows = m.run_sql(case["sql"])
    assert as_json([cols, rows]) == case["result"]


def test_run_sql_error_raises():
    with pytest.raises(sqlite3.Error):
        m.run_sql("SELECT nope FROM customers")


@pytest.mark.parametrize("case", SNAP["same_result"], ids=[f"pair{i}" for i in range(len(SNAP["same_result"]))])
def test_same_result_snapshot(case):
    assert m.same_result(case["sql"], case["expected"]) is case["result"]


# --- 루프 종료 검사 에이전트 -------------------------------------------------------
async def _collect(agent, state):
    ctx = SimpleNamespace(session=SimpleNamespace(state=state), invocation_id="inv-1")
    return [e async for e in agent._run_async_impl(ctx)]


@pytest.mark.parametrize("state,escalate", [
    ({"feedback": "PASS"}, True),
    ({"feedback": "  pass\n"}, True),
    ({"feedback": "PASSED with note"}, True),
    ({"feedback": "FAIL: no such column"}, False),
    ({}, False),
    ({"feedback": None}, False),
])
def test_exit_condition_checker(state, escalate):
    checker = m.ExitConditionChecker(name="X", condition_key="feedback", exit_condition="PASS")
    events = asyncio.run(_collect(checker, state))
    assert len(events) == 1
    assert events[0].author == "X" and events[0].invocation_id == "inv-1"
    assert events[0].actions.escalate is escalate


# --- 에이전트 구성 -------------------------------------------------------------
def test_agent_structure():
    assert m.root_agent is m.loop
    assert m.loop.name == "ValidationLoop" and m.loop.max_iterations == m.MAX_ITERATIONS
    assert [a.name for a in m.loop.sub_agents] == ["Generator", "Critic", "ExitConditionChecker"]
    checker = m.loop.sub_agents[2]
    assert isinstance(checker, m.ExitConditionChecker)
    assert (checker.condition_key, checker.exit_condition) == ("feedback", "PASS")
    assert m.generator.output_key == "draft" and m.critic.output_key == "feedback"
    assert [t.__name__ for t in m.critic.tools] == ["validate_sql"]
    assert "{feedback?}" in m.generator.instruction and "{draft?}" in m.generator.instruction
    assert "{draft}" in m.critic.instruction and "{question}" in m.critic.instruction
    assert m.generator.model is m.MODEL and m.critic.model is m.MODEL


def test_solve_is_async():
    assert inspect.iscoroutinefunction(m.solve)


def test_load_questions():
    qs = m.load_questions()
    assert [q["id"] for q in qs] == list(range(1, 9))
    assert all(q.get("expected_sql") for q in qs)


# --- show / main (모델 호출 대신 정답 SQL을 돌려주는 가짜 run_safe 사용) -------------------
def _fake_run_safe(sql_for):
    def run(coro):
        question = coro.cr_frame.f_locals["question"]
        coro.close()
        return {"sql": sql_for(question), "passed": True, "iterations": 2}
    return run


def _answers():
    return {q["question"]: q["expected_sql"] for q in m.load_questions()}


def test_show_with_expected(monkeypatch, capsys):
    monkeypatch.setattr(m, "run_safe", _fake_run_safe(lambda q: _answers()[q]))
    q = m.load_questions()[0]
    r = m.show(q, q["question"])
    assert r == {"sql": q["expected_sql"], "passed": True, "iterations": 2, "correct": True}
    out = capsys.readouterr().out
    assert f"▶ 질문 #1 ({q['level']}): {q['question']}" in out
    assert "📊 최종 SQL 실행 결과" in out and "🎯 정답 비교: 일치" in out


def test_show_free_question_with_bad_sql(monkeypatch, capsys):
    monkeypatch.setattr(m, "run_safe", _fake_run_safe(lambda q: "SELECT nope FROM customers"))
    r = m.show(None, "아무 질문")
    assert "correct" not in r
    out = capsys.readouterr().out
    assert "▶ 질문: 아무 질문" in out and "📊 최종 SQL 실행 실패" in out and "🎯" not in out


def test_main_lists_questions(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["x.py"])
    m.main()
    out = capsys.readouterr().out
    assert out.startswith("문제 목록 (python adk_generator_critic.py <번호|all|\"직접 질문\">)")
    assert out.count("\n  ") == 8


def test_main_unknown_number(monkeypatch):
    monkeypatch.setattr("sys.argv", ["x.py", "99"])
    with pytest.raises(SystemExit) as exc:
        m.main()
    assert str(exc.value).startswith("99번 문제가 없습니다")


def test_main_number(monkeypatch, capsys):
    monkeypatch.setattr(m, "run_safe", _fake_run_safe(lambda q: _answers()[q]))
    monkeypatch.setattr("sys.argv", ["x.py", "4"])
    m.main()
    assert "▶ 질문 #4" in capsys.readouterr().out


def test_main_all_summary(monkeypatch, capsys):
    answers = _answers()
    first = m.load_questions()[0]["question"]
    monkeypatch.setattr(m, "run_safe", _fake_run_safe(lambda q: "SELECT 1" if q == first else answers[q]))
    monkeypatch.setattr("sys.argv", ["x.py", "all"])
    m.main()
    out = capsys.readouterr().out
    assert "📋 채점 요약" in out
    assert "정답 7/8, 평균 반복 2.0회" in out


def test_main_free_question(monkeypatch, capsys):
    monkeypatch.setattr(m, "run_safe", _fake_run_safe(lambda q: "SELECT COUNT(*) FROM customers"))
    monkeypatch.setattr("sys.argv", ["x.py", "VIP", "고객", "수는?"])
    m.main()
    assert "▶ 질문: VIP 고객 수는?" in capsys.readouterr().out


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


@pytest.mark.parametrize("msg,expected", [("429 RESOURCE_EXHAUSTED", "⏳"), ("invalid api key", "❌ API 키 인증 실패")])
def test_run_safe_errors(no_keys, fresh_ready, monkeypatch, msg, expected):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    with pytest.raises(SystemExit) as exc:
        m.run_safe(_boom(msg))
    assert str(exc.value).startswith(expected)
