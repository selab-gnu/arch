"""클라우드 서비스. 엣지 노드가 보낸 요약 데이터를 모아 전체 현황을 제공한다.

실행:  python cloud_service.py   (python/edge 폴더에서)
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List

PORT = 6001

SUMMARIES: List[Dict[str, Any]] = []


class CloudHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/summaries":
            self._send_json(200, SUMMARIES)
        else:
            self._send_json(404, {"error": "unknown path"})

    def do_POST(self) -> None:
        if self.path != "/summaries":
            self._send_json(404, {"error": "unknown path"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            summary = json.loads(self.rfile.read(length))
        except ValueError:
            self._send_json(400, {"error": "invalid json"})
            return
        SUMMARIES.append(summary)
        self._send_json(201, summary)

    def _send_json(self, status: int, body: Any) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    print(f"cloud service on http://localhost:{PORT}")
    HTTPServer(("localhost", PORT), CloudHandler).serve_forever()


if __name__ == "__main__":
    main()
