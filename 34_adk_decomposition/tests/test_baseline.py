"""안전망 테스트 — 분리 작업 전의 동작을 그대로 고정합니다.

값이 이상해 보여도 고치지 않습니다. 분리 후에도 결과가 똑같은지만 확인합니다.
실제 모델 호출은 하지 않습니다(.refactor/manual_check.md 참고).
"""

import inspect
import json
import re
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import adk_hierarchical_report as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
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
    "APP_NAME", "BASE_DIR", "CORPUS_PATH", "REPORT_DIR", "DEFAULT_TOPIC",
    "_load_corpus", "search_web", "LEVEL", "_T0", "_log", "on_agent_start", "on_agent_end", "on_tool_call",
    "build_report_writer", "SEARCH_MODE", "root_agent", "write_report", "main",
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
    assert m.APP_NAME == "hierarchical_report_app"
    assert m.BASE_DIR == ROOT
    assert m.CORPUS_PATH == ROOT / "data" / "web_corpus.json"
    assert m.REPORT_DIR == ROOT / "reports"
    assert m.DEFAULT_TOPIC == "2026년 AI 트렌드"
    assert m.LEVEL == {"ReportWriter": 1, "ResearchAssistant": 2, "WebSearchAgent": 3, "SummarizerAgent": 3}


# --- 가상 웹 검색 --------------------------------------------------------------
def test_load_corpus():
    docs = m._load_corpus()
    assert docs == json.loads(m.CORPUS_PATH.read_text(encoding="utf-8"))["documents"]
    assert len(docs) == 12


SNAPSHOTS = json.loads((HERE / "search_snapshots.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", SNAPSHOTS, ids=[c["query"] for c in SNAPSHOTS])
def test_search_web_snapshot(case):
    assert m.search_web(case["query"], case["max_results"]) == case["result"]


def test_search_web_default_max_results():
    assert m.search_web("AI 에이전트 기업 도입") == SNAPSHOTS[0]["result"]


# --- 실행 추적 콜백 -------------------------------------------------------------
LINE = re.compile(r"^\s*\d+\.\d+s  (?P<rest>.*)$")


def _lines(out):
    return [LINE.match(x).group("rest") for x in out.strip().splitlines()]


def test_trace_callbacks(capsys):
    m.on_agent_start(SimpleNamespace(agent_name="ReportWriter"))
    m.on_agent_start(SimpleNamespace(agent_name="ResearchAssistant"))
    m.on_tool_call(SimpleNamespace(name="search_web"), {"query": "AI 에이전트"}, SimpleNamespace(agent_name="WebSearchAgent"))
    m.on_tool_call(SimpleNamespace(name="ResearchAssistant"), {"request": "x" * 80}, SimpleNamespace(agent_name="ReportWriter"))
    m.on_tool_call(SimpleNamespace(name="t"), {}, SimpleNamespace(agent_name="Unknown"))
    m.on_agent_end(SimpleNamespace(agent_name="SummarizerAgent"))
    m.on_agent_end(SimpleNamespace(agent_name="ReportWriter"))
    assert _lines(capsys.readouterr().out) == [
        "[L1 ReportWriter] 시작",
        "    [L2 ResearchAssistant] 시작",
        "        [L3 WebSearchAgent] 🔧 search_web('AI 에이전트')",
        f"[L1 ReportWriter] 🔧 ResearchAssistant({'x' * 60!r})",
        "[L? Unknown] 🔧 t('')",
        "        [L3 SummarizerAgent] 완료 → 결과를 호출한 쪽으로 반환",
        "[L1 ReportWriter] 완료 → 최종 보고서 작성",
    ]


def test_trace_time_resets(capsys):
    saved = m._T0[0]
    try:
        m._T0[0] = time.perf_counter() - 12.34
        m._log("ReportWriter", "x")
    finally:
        m._T0[0] = saved
    assert capsys.readouterr().out.startswith("  12.3s  [L1 ReportWriter] x")


# --- 에이전트 계층 -------------------------------------------------------------
def _tree(agent):
    return {"name": agent.name, "model_is_shared": agent.model is m.MODEL,
            "callbacks": (agent.before_agent_callback, agent.after_agent_callback, agent.before_tool_callback),
            "tools": [(type(t).__name__, getattr(t, "name", getattr(t, "__name__", None))) for t in agent.tools],
            "children": [_tree(t.agent) for t in agent.tools if type(t).__name__ == "AgentTool"]}


@pytest.mark.parametrize("live", [False, True])
def test_build_report_writer(live):
    root = _tree(m.build_report_writer(live=live))
    hooks = (m.on_agent_start, m.on_agent_end, m.on_tool_call)
    assert root["name"] == "ReportWriter" and root["tools"] == [("AgentTool", "ResearchAssistant")]
    l2 = root["children"][0]
    assert l2["tools"] == [("AgentTool", "WebSearchAgent"), ("AgentTool", "SummarizerAgent")]
    web, summ = l2["children"]
    assert web["tools"] == ([("GoogleSearchTool", "google_search")] if live else [("function", "search_web")])
    assert summ["tools"] == []
    for node in (root, l2, web, summ):
        assert node["model_is_shared"] and node["callbacks"] == hooks


def test_root_agent_default_local():
    assert m.SEARCH_MODE == "local"
    assert m.root_agent.name == "ReportWriter"


def test_write_report_is_async():
    assert inspect.iscoroutinefunction(m.write_report)


# --- main ----------------------------------------------------------------------
def _fake_run_safe(captured):
    def run(coro):
        captured.append(coro.cr_frame.f_locals.copy())
        coro.close()
        return "# 보고서\n본문"
    return run


def test_main_saves_report(monkeypatch, tmp_path, capsys):
    calls = []
    monkeypatch.setattr(m, "run_safe", _fake_run_safe(calls))
    monkeypatch.setattr(m, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr("sys.argv", ["x.py", "AI", "보안"])
    m.main()
    assert calls == [{"topic": "AI 보안", "live": False}]
    files = list((tmp_path / "reports").glob("report_*.md"))
    assert len(files) == 1 and re.fullmatch(r"report_\d{8}_\d{6}\.md", files[0].name)
    assert files[0].read_text(encoding="utf-8") == "# 보고서\n본문\n"
    out = capsys.readouterr().out
    assert "▶ 주제: AI 보안" in out and "▶ 검색 모드: 가상 웹 (data/web_corpus.json)" in out and "💾 저장:" in out


def test_main_default_topic_no_save(monkeypatch, tmp_path, capsys):
    calls = []
    monkeypatch.setattr(m, "run_safe", _fake_run_safe(calls))
    monkeypatch.setattr(m, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr("sys.argv", ["x.py", "--no-save"])
    m.main()
    assert calls == [{"topic": "2026년 AI 트렌드", "live": False}]
    assert not (tmp_path / "reports").exists()


def test_main_empty_report_not_saved(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(m, "run_safe", lambda coro: (coro.close(), "")[1])
    monkeypatch.setattr(m, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr("sys.argv", ["x.py"])
    m.main()
    assert "(보고서를 받지 못했습니다)" in capsys.readouterr().out
    assert not (tmp_path / "reports").exists()


def test_main_live_requires_gemini(monkeypatch):
    monkeypatch.setattr(m, "MODEL_PROVIDER", "claude")
    monkeypatch.setattr("sys.argv", ["x.py", "--live"])
    with pytest.raises(SystemExit) as exc:
        m.main()
    assert str(exc.value).startswith("--live(실제 웹 검색)는 Gemini 내장 google_search 도구라서")


def test_main_live_with_gemini(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(m, "MODEL_PROVIDER", "gemini")
    monkeypatch.setattr(m, "run_safe", _fake_run_safe(calls))
    monkeypatch.setattr("sys.argv", ["x.py", "트렌드", "--live", "--no-save"])
    m.main()
    assert calls == [{"topic": "트렌드", "live": True}]
    assert "실제 웹 (google_search)" in capsys.readouterr().out


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
    return "ok"


async def _boom(msg):
    raise RuntimeError(msg)


def test_run_safe_no_key(no_keys, fresh_ready):
    coro = _ok()
    with pytest.raises(SystemExit):
        m.run_safe(coro)
    assert coro.cr_frame is None


def test_run_safe_ok_once(no_keys, fresh_ready, monkeypatch, capsys):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert m.run_safe(_ok()) == "ok" and m.run_safe(_ok()) == "ok"
    assert capsys.readouterr().out.count("🧠 사용 모델:") == 1


@pytest.mark.parametrize("msg,expected", [("529 overloaded", "⏳"), ("PERMISSION_DENIED", "❌ API 키 인증 실패")])
def test_run_safe_errors(no_keys, fresh_ready, monkeypatch, msg, expected):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    with pytest.raises(SystemExit) as exc:
        m.run_safe(_boom(msg))
    assert str(exc.value).startswith(expected)


# --- 실행 시작 시각(_T0) 공유 — 4단계(trace_callbacks.py 분리)에서 추가 -------------------
def test_write_report_resets_shared_start_time(monkeypatch, capsys):
    import asyncio
    import trace_callbacks

    assert m._T0 is trace_callbacks._T0  # 두 파일이 같은 리스트를 가리킴

    class FakeSessionService:
        async def create_session(self, **kw):
            return SimpleNamespace(id="s1")

    class FakeRunner:  # 모델을 부르지 않는 가짜 러너: 이벤트 없이 바로 끝남
        def __init__(self, **kw):
            self.session_service = FakeSessionService()

        async def run_async(self, **kw):
            trace_callbacks.on_agent_start(SimpleNamespace(agent_name="ReportWriter"))
            return
            yield

    saved = m._T0[0]
    try:
        m._T0[0] = time.perf_counter() - 1000  # 아주 오래전 시각으로 만들어 둠
        monkeypatch.setattr(m, "InMemoryRunner", FakeRunner)
        assert asyncio.run(m.write_report("주제", live=False)) == ""
    finally:
        m._T0[0] = saved
    # write_report가 시작 시각을 '지금'으로 다시 맞췄다면 콜백 출력은 0초 근처여야 함
    assert capsys.readouterr().out.startswith("   0.0s  [L1 ReportWriter] 시작")
