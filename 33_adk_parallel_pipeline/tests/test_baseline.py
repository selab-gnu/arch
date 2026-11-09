"""안전망 테스트 — 분리 작업 전의 동작을 그대로 고정합니다.

값이 이상해 보여도 고치지 않습니다. 분리 후에도 결과가 똑같은지만 확인합니다.
실제 모델 호출은 하지 않습니다(.refactor/manual_check.md 참고).
"""

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import adk_parallel_code_review as m

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
    "APP_NAME", "BASE_DIR", "DEFAULT_TARGET", "REVIEW_DIR",
    "SECURITY_RULES", "scan_security_patterns", "run_pep8_check", "analyze_complexity",
    "REVIEW_FORMAT", "security_scanner", "style_checker", "complexity_analyzer", "parallel_reviews",
    "pr_summarizer", "workflow", "root_agent", "numbered", "review_file", "collect_targets", "main",
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


def test_resolve_model_default_gemini(no_keys):
    model, label, provider = m.resolve_model()
    assert (type(model).__name__, label, provider) == ("Gemini", "Gemini (gemini-3.8-flash)", "gemini")


def test_resolve_model_claude_on_vertex(no_keys, monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "1")
    monkeypatch.setenv("ADK_MODEL", "claude-opus-5-5")
    assert m.resolve_model() == ("claude-opus-5-5", "Claude (claude-opus-5-5, Vertex AI)", "claude")


def test_resolve_model_bad_provider(no_keys, monkeypatch):
    monkeypatch.setenv("ADK_PROVIDER", "nope")
    with pytest.raises(SystemExit):
        m.resolve_model()


# --- 경로 / 상수 ---------------------------------------------------------------
def test_paths_and_constants():
    assert m.APP_NAME == "parallel_code_review_app"
    assert m.BASE_DIR == ROOT
    assert m.DEFAULT_TARGET == ROOT / "data" / "pr_samples" / "user_service.py"
    assert m.REVIEW_DIR == ROOT / "reviews"
    assert len(m.SECURITY_RULES) == 8


# --- 정적 분석 도구 (샘플 3개 + 경계 사례 2개의 결과를 그대로 고정) --------------------
SNAPSHOTS = json.loads((HERE / "tool_snapshots.json").read_text(encoding="utf-8"))
TOOLS = ("scan_security_patterns", "run_pep8_check", "analyze_complexity")


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("name", list(SNAPSHOTS))
def test_tool_snapshot(name, tool):
    ctx = SimpleNamespace(state={"code_raw": SNAPSHOTS[name]["code"]})
    assert getattr(m, tool)(ctx) == SNAPSHOTS[name][tool]


@pytest.mark.parametrize("name", ["clean_stats.py", "report_utils.py", "user_service.py"])
def test_snapshot_matches_sample_file(name):
    assert (ROOT / "data" / "pr_samples" / name).read_text(encoding="utf-8") == SNAPSHOTS[name]["code"]


@pytest.mark.parametrize("tool", TOOLS)
def test_tools_with_empty_state(tool):
    r = getattr(m, tool)(SimpleNamespace(state={}))
    assert r["status"] == "success"


# --- 에이전트 구성 -------------------------------------------------------------
def test_agent_structure():
    assert m.root_agent is m.workflow
    assert [a.name for a in m.workflow.sub_agents] == ["CodeReviewSwarm", "PRSummarizer"]
    assert [a.name for a in m.parallel_reviews.sub_agents] == ["SecurityAuditor", "StyleEnforcer", "PerformanceAnalyst"]
    assert [a.output_key for a in m.parallel_reviews.sub_agents] == ["security_report", "style_report", "performance_report"]
    assert [[t.__name__ for t in a.tools] for a in m.parallel_reviews.sub_agents] == [
        ["scan_security_patterns"], ["run_pep8_check"], ["analyze_complexity"]]
    assert m.pr_summarizer.output_key == "pr_review"
    for key in ("{security_report}", "{style_report}", "{performance_report}", "{file_name}"):
        assert key in m.pr_summarizer.instruction
    assert all(m.REVIEW_FORMAT in a.instruction for a in m.parallel_reviews.sub_agents)
    assert all(a.model is m.MODEL for a in (*m.parallel_reviews.sub_agents, m.pr_summarizer))


# --- 실행 도우미 ---------------------------------------------------------------
def test_numbered():
    assert m.numbered("a\nb") == "   1 | a\n   2 | b"
    assert m.numbered("") == ""


def test_collect_targets(tmp_path):
    assert m.collect_targets([]) == [m.DEFAULT_TARGET]
    (tmp_path / "b.py").write_text("")
    (tmp_path / "a.py").write_text("")
    (tmp_path / "c.txt").write_text("")
    assert m.collect_targets([str(tmp_path), "x.py"]) == [tmp_path / "a.py", tmp_path / "b.py", Path("x.py")]


def test_review_file_is_async():
    assert inspect.iscoroutinefunction(m.review_file)


FAKE_STATE = {"security_report": "SEC", "style_report": "STY", "performance_report": "PERF", "pr_review": "PR"}


def _fake_run_safe(coro):
    coro.close()
    return dict(FAKE_STATE)


def test_main_saves_review(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(m, "run_safe", _fake_run_safe)
    monkeypatch.setattr(m, "REVIEW_DIR", tmp_path / "reviews")
    monkeypatch.setattr("sys.argv", ["x.py", str(m.DEFAULT_TARGET)])
    m.main()
    out = (tmp_path / "reviews" / "user_service_review.md").read_text(encoding="utf-8")
    assert out == ("# PR 리뷰: user_service.py\n\nPR\n\n---\n\n## 🔒 보안 리뷰\n\nSEC\n\n"
                   "## 🎨 스타일 리뷰\n\nSTY\n\n## ⚡ 성능 리뷰\n\nPERF\n")
    printed = capsys.readouterr().out
    assert "📝 PRSummarizer — 최종 PR 리뷰" in printed and "💾 저장:" in printed


def test_main_no_save(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(m, "run_safe", _fake_run_safe)
    monkeypatch.setattr(m, "REVIEW_DIR", tmp_path / "reviews")
    monkeypatch.setattr("sys.argv", ["x.py", "--no-save"])
    m.main()
    assert not (tmp_path / "reviews").exists()
    assert "💾" not in capsys.readouterr().out


# --- 오류 안내 / 안전 실행 --------------------------------------------------------
def test_transient_error_message():
    assert m.transient_error_message(RuntimeError("503 UNAVAILABLE"), "L").startswith(
        "⏳ 모델 서버가 일시적으로 응답하지 못했습니다 (L)\n   503 UNAVAILABLE\n")
    assert m.transient_error_message(ValueError("bad"), "L") is None


def test_error_text_chain():
    try:
        try:
            raise ValueError("inner")
        except ValueError as inner:
            raise RuntimeError("outer") from inner
    except RuntimeError as e:
        assert m._error_text(e) == "RuntimeError: outer | ValueError: inner"


def test_check_api_key(no_keys, monkeypatch):
    with pytest.raises(SystemExit):
        m.check_api_key()
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert m.check_api_key() is None


async def _ok():
    return 7


async def _boom(msg):
    raise RuntimeError(msg)


def test_run_safe_no_key(no_keys, fresh_ready):
    coro = _ok()
    with pytest.raises(SystemExit):
        m.run_safe(coro)
    assert coro.cr_frame is None


def test_run_safe_ok_once(no_keys, fresh_ready, monkeypatch, capsys):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert m.run_safe(_ok()) == 7 and m.run_safe(_ok()) == 7
    assert capsys.readouterr().out.count("🧠 사용 모델:") == 1


@pytest.mark.parametrize("msg,expected", [("429 RESOURCE_EXHAUSTED", "⏳"), ("401 Unauthorized", "❌ API 키 인증 실패")])
def test_run_safe_errors(no_keys, fresh_ready, monkeypatch, msg, expected):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    with pytest.raises(SystemExit) as exc:
        m.run_safe(_boom(msg))
    assert str(exc.value).startswith(expected)


def test_run_safe_other_errors_propagate(no_keys, fresh_ready, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    with pytest.raises(RuntimeError):
        m.run_safe(_boom("other"))
