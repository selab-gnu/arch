"""안전망 테스트 — 분리 작업 전의 동작을 그대로 고정합니다.

값이 이상해 보여도 고치지 않습니다. 분리 후에도 결과가 똑같은지만 확인합니다.
실제 모델 호출은 하지 않습니다(.refactor/manual_check.md 참고). 실행 시간(ms)은 매번 달라서 비교하지 않습니다.
"""

import asyncio
import inspect
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import adk_iterative_refinement as m
from tests_solutions import CASES, FAST, NAIVE_COUNT_PAIRS

ROOT = Path(__file__).resolve().parent.parent
TASKS = {t["func"]: t for t in m.load_tasks()}
KEY_VARS = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI",
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ADK_MODEL", "ADK_PROVIDER")


def no_ms(d):
    return {k: v for k, v in d.items() if k != "ms"}


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
    "APP_NAME", "BASE_DIR", "TASKS_PATH", "RESULT_DIR", "MAX_ITERATIONS", "BENCH_TIMEOUT", "ENABLE_QUALITY_GATE",
    "load_tasks", "clean_code", "HARNESS", "benchmark", "benchmark_current_draft", "QualityGate",
    "generator", "critic", "refiner", "loop", "workflow", "root_agent",
    "task_prompt", "fmt", "optimize", "report", "main",
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
    assert m.APP_NAME == "iterative_refinement_app"
    assert m.BASE_DIR == ROOT
    assert m.TASKS_PATH == ROOT / "data" / "tasks.json"
    assert m.RESULT_DIR == ROOT / "results"
    assert (m.MAX_ITERATIONS, m.BENCH_TIMEOUT, m.ENABLE_QUALITY_GATE) == (3, 10.0, True)


def test_load_tasks():
    assert [(t["id"], t["func"], t["target_ms"]) for t in m.load_tasks()] == [
        (1, "count_pairs", 20), (2, "primes_up_to", 40), (3, "climb_ways", 40)]


# --- 코드 정리 / 벤치마크 ---------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("```python\ndef f():\n    return 1\n```", "def f():\n    return 1"),
    ("설명\n```py\nx = 1\n```\n끝", "x = 1"),
    ("```\ny = 2\n```", "y = 2"),
    ("  def g(): pass  ", "def g(): pass"),
    ("", ""),
])
def test_clean_code(text, expected):
    assert m.clean_code(text) == expected


@pytest.mark.parametrize("func", list(FAST))
def test_benchmark_fast_solutions(func):
    r = m.benchmark(FAST[func], TASKS[func])
    assert set(r) == {"correct", "ms"} and r["correct"] is True
    assert isinstance(r["ms"], float) and r["ms"] >= 0


EXPECTED_FAILURES = {
    "wrong_answer": "오답: count_pairs([1, 5, 7, -1], 6) → 0 (기대값 2)",
    "syntax_error": "SyntaxError: expected ':' (<string>, line 1)",
    "missing_func": "KeyError: 'count_pairs'",
    "runtime_error": "ZeroDivisionError: division by zero",
    "big_input_wrong": "성능 측정용 큰 입력에서 결과가 틀림",
    "recursion": "RecursionError: 재귀가 너무 깊음 (큰 입력에서 재귀 대신 반복문/DP 필요)",
    "no_output": "실행 실패",
}


@pytest.mark.parametrize("label,func,code", CASES, ids=[c[0] for c in CASES])
def test_benchmark_failures(label, func, code):
    r = m.benchmark(code, TASKS[func])
    assert no_ms(r) == {"correct": False, "error": EXPECTED_FAILURES[label]}
    assert ("ms" in r) is (label == "big_input_wrong")


def test_benchmark_timeout(monkeypatch):
    # benchmark 함수가 들어 있는 모듈의 BENCH_TIMEOUT을 바꿉니다(분리 후에도 같은 테스트가 동작하도록).
    monkeypatch.setitem(m.benchmark.__globals__, "BENCH_TIMEOUT", 0.5)
    assert m.benchmark(NAIVE_COUNT_PAIRS, TASKS["count_pairs"]) == {
        "correct": False, "error": "시간 초과: 0초 안에 끝나지 않음 (복잡도 개선 필요)"}


def test_harness_is_isolated_script():
    assert m.HARNESS.lstrip().startswith("import json, sys, time")
    assert 'print(json.dumps(out, ensure_ascii=False))' in m.HARNESS


def test_benchmark_current_draft_records_history():
    t = TASKS["primes_up_to"]
    state = {"task_json": __import__("json").dumps(t, ensure_ascii=False),
             "current_draft": "```python\n" + FAST["primes_up_to"] + "```", "history": []}
    ctx = SimpleNamespace(state=state)
    r1 = m.benchmark_current_draft(ctx)
    state["current_draft"] = CASES[0][2]
    r2 = m.benchmark_current_draft(ctx)
    assert r1["correct"] is True and r1["target_ms"] == 40
    # 두 번째 초안은 count_pairs 함수라서 primes_up_to를 찾지 못함
    assert r2 == {"correct": False, "error": "KeyError: 'primes_up_to'", "target_ms": 40}
    assert [h["version"] for h in state["history"]] == [1, 2]
    assert state["benchmark"] is r2
    assert no_ms(state["history"][0]) == {"version": 1, "correct": True, "target_ms": 40}


# --- 품질 관문 (조기 종료) -----------------------------------------------------------
async def _collect(agent, state):
    ctx = SimpleNamespace(session=SimpleNamespace(state=state), invocation_id="inv-1")
    return [e async for e in agent._run_async_impl(ctx)]


@pytest.mark.parametrize("bench,escalate", [
    ({"correct": True, "ms": 5.0, "target_ms": 20}, True),
    ({"correct": True, "ms": 20.0, "target_ms": 20}, True),
    ({"correct": True, "ms": 25.0, "target_ms": 20}, False),
    ({"correct": False, "ms": 1.0, "target_ms": 20}, False),
    ({"correct": True, "target_ms": 20}, False),
    (None, False),
])
def test_quality_gate(bench, escalate):
    state = {} if bench is None else {"benchmark": bench}
    events = asyncio.run(_collect(m.QualityGate(name="QG"), state))
    assert len(events) == 1 and events[0].author == "QG" and events[0].invocation_id == "inv-1"
    assert events[0].actions.escalate is escalate


def test_quality_gate_disabled(monkeypatch):
    monkeypatch.setattr(m, "ENABLE_QUALITY_GATE", False)
    events = asyncio.run(_collect(m.QualityGate(name="QG"), {"benchmark": {"correct": True, "ms": 1, "target_ms": 20}}))
    assert events[0].actions.escalate is False


# --- 에이전트 구성 -------------------------------------------------------------
def test_agent_structure():
    assert m.root_agent is m.workflow
    assert [a.name for a in m.workflow.sub_agents] == ["Generator", "RefinementLoop"]
    assert m.loop.max_iterations == m.MAX_ITERATIONS
    assert [a.name for a in m.loop.sub_agents] == ["Critic", "QualityGate", "Refiner"]
    assert isinstance(m.loop.sub_agents[1], m.QualityGate)
    assert (m.generator.output_key, m.critic.output_key, m.refiner.output_key) == (
        "current_draft", "critique_notes", "current_draft")
    assert [t.__name__ for t in m.critic.tools] == ["benchmark_current_draft"]
    assert "{current_draft}" in m.refiner.instruction and "{critique_notes}" in m.refiner.instruction
    assert all(a.model is m.MODEL for a in (m.generator, m.critic, m.refiner))


# --- 실행 도우미 ---------------------------------------------------------------
def test_task_prompt():
    t = TASKS["count_pairs"]
    p = m.task_prompt(t)
    assert p.startswith(f"[과제] {t['description']}\n시그니처: {t['signature']}\n예시:\n")
    assert p.endswith("성능 목표: 큰 입력에서 20ms 이내")
    assert p.count("  count_pairs(") == 3


@pytest.mark.parametrize("b,expected", [
    ({"correct": True, "ms": 1.234, "target_ms": 40}, "✅ 정답, 1.2ms 🎯(목표 40ms)"),
    ({"correct": True, "ms": 100, "target_ms": 40}, "✅ 정답, 100.0ms   (목표 40ms)"),
    ({"correct": False}, "❌ 실패"),
    ({"correct": False, "error": "x"}, "❌ x"),
])
def test_fmt(b, expected):
    assert m.fmt(b) == expected


def test_optimize_is_async():
    assert inspect.iscoroutinefunction(m.optimize)


def _h(v, correct, ms=None, target=40, error=None):
    d = {"version": v, "correct": correct, "target_ms": target}
    if ms is not None:
        d["ms"] = ms
    if error:
        d["error"] = error
    return d


def test_report_improvement_and_save(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(m, "RESULT_DIR", tmp_path / "results")
    t = TASKS["primes_up_to"]
    m.report(t, {"code": "def primes_up_to(n): ...", "history": [_h(1, True, 800.0), _h(2, True, 8.0)]})
    out = capsys.readouterr().out
    assert "📈 버전별 개선 추이 (primes_up_to)" in out and "→ 첫 정답 버전 대비 100.0배 빨라짐" in out
    assert "⚠️" not in out
    saved = (tmp_path / "results" / "primes_up_to_optimized.py").read_text(encoding="utf-8")
    assert saved == "# 최종 버전 (v2) — ✅ 정답, 8.0ms 🎯(목표 40ms)\ndef primes_up_to(n): ...\n"


def test_report_warns_when_last_version_worse(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(m, "RESULT_DIR", tmp_path / "results")
    m.report(TASKS["primes_up_to"], {"code": "x", "history": [_h(1, True, 100.0), _h(2, True, 5.0), _h(3, False, error="오답")]})
    out = capsys.readouterr().out
    assert "⚠️  최종 버전(v3)이 가장 좋았던 v2보다 나쁩니다" in out


def test_report_no_code_not_saved(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(m, "RESULT_DIR", tmp_path / "results")
    m.report(TASKS["count_pairs"], {"code": "", "history": []})
    assert not (tmp_path / "results").exists()


def test_main_lists_tasks(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["x.py"])
    m.main()
    out = capsys.readouterr().out
    assert out.startswith("과제 목록 (python adk_iterative_refinement.py <번호|all>)")
    assert len(re.findall(r"^  \d\. ", out, re.M)) == 3


def test_main_unknown_task(monkeypatch):
    monkeypatch.setattr("sys.argv", ["x.py", "9"])
    with pytest.raises(SystemExit) as exc:
        m.main()
    assert str(exc.value).startswith("9번 과제가 없습니다")


@pytest.mark.parametrize("arg,expected", [("2", ["primes_up_to"]), ("all", ["count_pairs", "primes_up_to", "climb_ways"])])
def test_main_runs_targets(monkeypatch, capsys, arg, expected):
    seen = []

    def fake_run_safe(coro):
        seen.append(coro.cr_frame.f_locals["t"]["func"])
        coro.close()
        return {"code": "", "history": []}

    monkeypatch.setattr(m, "run_safe", fake_run_safe)
    monkeypatch.setattr("sys.argv", ["x.py", arg])
    m.main()
    assert seen == expected
    assert "QualityGate 켜짐" in capsys.readouterr().out


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


@pytest.mark.parametrize("msg,expected", [("503 overloaded", "⏳"), ("401 Unauthorized", "❌ API 키 인증 실패")])
def test_run_safe_errors(no_keys, fresh_ready, monkeypatch, msg, expected):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    with pytest.raises(SystemExit) as exc:
        m.run_safe(_boom(msg))
    assert str(exc.value).startswith(expected)
