"""버그 수정 확인 — 여러 건을 이어서 실행해도 같은 이벤트 루프(실행기)를 쓰는지.

예전에는 건마다 asyncio.run()으로 새 루프를 만들었습니다. OpenAI·Claude 연결 도구(AsyncOpenAI / AsyncAnthropic)는
처음 만든 연결을 계속 재사용하므로, 두 번째 건부터 닫힌 루프의 연결을 쓰다가
`RuntimeError: Event loop is closed`로 멈췄습니다. (Gemini 도구는 루프마다 연결을 새로 만들어 영향 없음)
"""

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import adk_sequential_pipeline as m


class _FakeOpenAI(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # keep-alive: 연결이 풀(pool)에 남아 다음 요청에서 재사용됨

    def do_GET(self):
        body = json.dumps({"object": "list", "data": []}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_openai_client():
    """로컬 가짜 서버에 붙는 AsyncOpenAI 클라이언트 하나 (API 키·네트워크 불필요)."""
    openai = pytest.importorskip("openai")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _FakeOpenAI)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield openai.AsyncOpenAI(api_key="test-not-real", base_url=f"http://127.0.0.1:{srv.server_port}/v1")
    srv.shutdown()


async def _loop_id():
    return id(asyncio.get_running_loop())

from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TWO_PDFS = [str(DATA / "invoice_en.pdf"), str(DATA / "meeting_minutes_ko.pdf")]


def _patch_main(monkeypatch, body):
    async def fake_run_pipeline(pdf_path):
        return {"structured_data": "S", "summary": await body()}
    monkeypatch.setattr(m, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(m, "check_api_key", lambda: None)
    monkeypatch.setattr("sys.argv", ["x.py", *TWO_PDFS])


def test_main_reuses_one_event_loop(monkeypatch, capsys):
    loops = []

    async def body():
        loops.append(await _loop_id())
        return "Y"

    _patch_main(monkeypatch, body)
    m.main()
    assert len(loops) == 2 and loops[0] == loops[1]


def test_cached_client_survives_second_pdf(monkeypatch, capsys, fake_openai_client):
    async def body():
        await fake_openai_client.models.list()     # 예전: 두 번째 PDF에서 RuntimeError: Event loop is closed
        return "Y"

    _patch_main(monkeypatch, body)
    m.main()
    assert capsys.readouterr().out.count("최종 요약") == 2
