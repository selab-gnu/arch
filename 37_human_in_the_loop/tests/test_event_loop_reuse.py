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

import adk_human_in_the_loop as m


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


@pytest.fixture
def with_key(monkeypatch):
    for v in ("GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.setattr(m, "MODEL_PROVIDER", "gemini")
    monkeypatch.setattr(m, "MODEL_LABEL", "Gemini (test)")
    m._READY[0] = False
    yield
    m._READY[0] = False


def test_run_safe_reuses_one_event_loop(with_key):
    assert m.run_safe(_loop_id()) == m.run_safe(_loop_id()) == m.run_safe(_loop_id())


def test_cached_client_survives_second_run(with_key, fake_openai_client):
    m.run_safe(fake_openai_client.models.list())
    m.run_safe(fake_openai_client.models.list())   # 예전: RuntimeError: Event loop is closed
