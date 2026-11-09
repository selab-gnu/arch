"""안전망 테스트 — 분리 작업 전의 동작을 그대로 고정합니다.

값이 이상해 보여도 고치지 않습니다. 분리 후에도 결과가 똑같은지만 확인합니다.
네트워크·API 키가 필요한 실제 파이프라인 실행은 여기서 하지 않습니다(.refactor/manual_check.md 참고).
"""

import inspect
import hashlib
from pathlib import Path

import pytest

import adk_sequential_pipeline as m

DATA = Path(__file__).resolve().parent.parent / "data"
KEY_VARS = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI",
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ADK_MODEL", "ADK_PROVIDER")


@pytest.fixture
def no_keys(monkeypatch):
    for v in KEY_VARS:
        monkeypatch.delenv(v, raising=False)


# --- 기존 이름이 원래 파일에서 계속 불러와지는지 ---------------------------------
PUBLIC_NAMES = [
    "DEFAULT_MODELS", "_has_key", "_provider_of", "resolve_model", "MODEL", "MODEL_LABEL",
    "APP_NAME", "MAX_CHARS", "pdf_parser", "_PATTERNS", "regex_extractor", "summary_engine",
    "parser", "extractor", "summarizer", "pipeline", "root_agent", "make_sample_pdf",
    "run_pipeline", "DATA_DIR", "collect_pdfs", "TRANSIENT_ERROR_PATTERN", "_error_text",
    "transient_error_message", "check_api_key", "main",
]


@pytest.mark.parametrize("name", PUBLIC_NAMES)
def test_name_still_importable(name):
    assert hasattr(m, name)


# --- 모델 선택 ---------------------------------------------------------------
def test_default_models():
    assert m.DEFAULT_MODELS == {"gemini": "gemini-3.8-flash", "claude": "claude-sonnet-5-5", "openai": "gpt-5.6"}


@pytest.mark.parametrize("model,provider", [
    ("claude-opus-5-5", "claude"), ("gpt-5.6", "openai"), ("o4-mini", "openai"),
    ("gemini-3.8-flash", "gemini"), ("anything", "gemini"),
])
def test_provider_of(model, provider):
    assert m._provider_of(model) == provider


def test_has_key(no_keys, monkeypatch):
    assert not any(m._has_key(p) for p in ("gemini", "claude", "openai"))
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
    assert m._has_key("gemini")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert m._has_key("claude")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert m._has_key("openai")


def test_resolve_model_default_gemini(no_keys):
    model, label = m.resolve_model()
    assert type(model).__name__ == "Gemini"
    assert label == "Gemini (gemini-3.8-flash)"


def test_resolve_model_explicit_gemini(no_keys, monkeypatch):
    monkeypatch.setenv("ADK_MODEL", "gemini-3.5-flash-lite")
    assert m.resolve_model()[1] == "Gemini (gemini-3.5-flash-lite)"


def test_resolve_model_claude_on_vertex(no_keys, monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "1")
    monkeypatch.setenv("ADK_MODEL", "claude-opus-5-5")
    assert m.resolve_model() == ("claude-opus-5-5", "Claude (claude-opus-5-5, Vertex AI)")


def test_resolve_model_bad_provider(no_keys, monkeypatch):
    monkeypatch.setenv("ADK_PROVIDER", "nope")
    with pytest.raises(SystemExit):
        m.resolve_model()


def test_module_constants():
    assert m.APP_NAME == "pdf_pipeline_app"
    assert m.MAX_CHARS == 20_000


# --- 도구 -------------------------------------------------------------------
@pytest.mark.parametrize("stem,pages,length,digest", [
    ("invoice_en", 1, 611, "56fc17a02b6a6062"),
    ("meeting_minutes_ko", 1, 649, "f00d58eb38d3454b"),
    ("research_report_ko", 2, 947, "200e8022359e504b"),
    ("service_contract_ko", 1, 753, "a88b2783699c287d"),
])
def test_pdf_parser(stem, pages, length, digest):
    r = m.pdf_parser(str(DATA / f"{stem}.pdf"))
    assert (r["status"], r["page_count"], r["truncated"], len(r["text"])) == ("success", pages, False, length)
    assert hashlib.sha256(r["text"].encode()).hexdigest()[:16] == digest


def test_pdf_parser_missing(tmp_path):
    r = m.pdf_parser(str(tmp_path / "none.pdf"))
    assert r["status"] == "error" and "파일이 없습니다" in r["message"]


def test_regex_extractor_invoice():
    text = m.pdf_parser(str(DATA / "invoice_en.pdf"))["text"]
    assert m.regex_extractor(text) == {"status": "success", "entities": {
        "emails": ["billing@acmecloud.example", "support@acmecloud.example"],
        "urls": ["https://pay.acmecloud.example/inv-2026-1108"],
        "dates": ["2026-11-08", "2026-12-08"],
        "amounts": ["$3,600.00", "$46.00", "$299.00", "$3,945.00", "$394.50", "$4,339.50"],
        "phones": ["+1-415-555-0142"],
        "percentages": ["10%", "1.5%"],
    }}


def test_regex_extractor_korean_boundaries():
    e = m.regex_extractor("계약일 2026-11-15부터, 금액 1,200,000원, 연락처 02-123-4567, 이율 3.5%")["entities"]
    assert e["dates"] == ["2026-11-15"]
    assert e["amounts"] == ["1,200,000원"]
    assert e["phones"] == ["02-123-4567"]
    assert e["percentages"] == ["3.5%"]


def test_summary_engine_fenced_json():
    data = '```json\n{"title":"T","amounts":["$3,945.00","$4,339.50"],"parties":["A","B"],"contacts":{"emails":["a@b.c"]}}\n```'
    assert m.summary_engine(data) == {
        "status": "success",
        "top_level_keys": ["title", "amounts", "parties", "contacts"],
        "field_counts": {"amounts": 2, "parties": 2, "title": 1, "contacts": 1, "emails": 1},
        "amount_values": [3945.0, 4339.5],
        "max_amount": 4339.5,
    }


def test_summary_engine_bad_json():
    assert m.summary_engine("not json")["status"] == "error"


def test_summary_engine_list_json():
    r = m.summary_engine("[1, 2]")
    assert r["top_level_keys"] == [] and r["max_amount"] is None


# --- 에이전트 조립 라인 -------------------------------------------------------
def test_pipeline_structure():
    assert m.root_agent is m.pipeline
    assert m.pipeline.name == "PDFProcessingPipeline"
    assert [a.name for a in m.pipeline.sub_agents] == ["ParserAgent", "ExtractorAgent", "SummarizerAgent"]
    assert [a.output_key for a in m.pipeline.sub_agents] == ["raw_text", "structured_data", "summary"]
    assert [[t.__name__ for t in a.tools] for a in m.pipeline.sub_agents] == [
        ["pdf_parser"], ["regex_extractor"], ["summary_engine"]]
    assert "{raw_text}" in m.extractor.instruction
    assert "{structured_data}" in m.summarizer.instruction
    assert all(a.model is m.MODEL for a in m.pipeline.sub_agents)


def test_run_pipeline_is_async():
    assert inspect.iscoroutinefunction(m.run_pipeline)


# --- 샘플 PDF / 명령행 / 오류 안내 ---------------------------------------------
def test_make_sample_pdf(tmp_path):
    path = m.make_sample_pdf(tmp_path / "s.pdf")
    assert path == tmp_path / "s.pdf"
    text = m.pdf_parser(str(path))["text"]
    assert "INVOICE" in text and "$4,339.50" in text


def test_collect_pdfs_default():
    assert m.DATA_DIR == DATA
    assert m.collect_pdfs([]) == [DATA / "invoice_en.pdf"]


def test_collect_pdfs_dir_and_file():
    found = m.collect_pdfs([str(DATA), "x.pdf"])
    assert [p.name for p in found] == ["invoice_en.pdf", "meeting_minutes_ko.pdf",
                                       "research_report_ko.pdf", "service_contract_ko.pdf", "x.pdf"]


def test_error_text_chain():
    try:
        try:
            raise ValueError("inner")
        except ValueError as inner:
            raise RuntimeError("outer") from inner
    except RuntimeError as e:
        assert m._error_text(e) == "RuntimeError: outer | ValueError: inner"


def test_transient_error_message():
    msg = m.transient_error_message(RuntimeError("503 UNAVAILABLE high demand"), "L")
    assert msg.startswith("⏳ 모델 서버가 일시적으로 응답하지 못했습니다 (L)\n   503 UNAVAILABLE high demand\n")
    assert m.transient_error_message(ValueError("bad input"), "L") is None


def test_check_api_key(no_keys, monkeypatch):
    with pytest.raises(SystemExit):
        m.check_api_key()
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert m.check_api_key() is None
