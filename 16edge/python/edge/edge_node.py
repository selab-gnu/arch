"""엣지 노드. 센서 가까이에서 데이터를 처리하고, 요약만 클라우드로 보낸다.

실행:  python edge_node.py   (python/edge 폴더에서)
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List
from urllib.request import Request, urlopen

PORT = 6002
CLOUD_SERVICE_URL = "http://localhost:6001"
TEMPERATURE_LIMIT = 30.0
BATCH_SIZE = 5

BUFFER: List[float] = []  # 아직 요약하지 않은 측정값
PENDING: List[Dict[str, Any]] = []  # 클라우드로 아직 보내지 못한 요약


def decide_action(temperature: float) -> str:
    """클라우드를 거치지 않고 엣지에서 바로 판단한다."""
    return "cooling_on" if temperature > TEMPERATURE_LIMIT else "none"


def summarize(temperatures: List[float]) -> Dict[str, Any]:
    return {
        "count": len(temperatures),
        "average": round(sum(temperatures) / len(temperatures), 1),
        "max": max(temperatures),
    }


def send_to_cloud(summary: Dict[str, Any]) -> bool:
    request = Request(
        f"{CLOUD_SERVICE_URL}/summaries",
        data=json.dumps(summary).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=3):
            return True
    except OSError:
        return False


def flush_pending() -> None:
    # 클라우드에 연결되지 않으면 요약을 보관했다가 다음 기회에 순서대로 보낸다
    while PENDING and send_to_cloud(PENDING[0]):
        PENDING.pop(0)


def store_reading(temperature: float) -> None:
    BUFFER.append(temperature)
    if len(BUFFER) >= BATCH_SIZE:
        PENDING.append(summarize(BUFFER))
        BUFFER.clear()
        flush_pending()


class EdgeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/status":
            self._send_json(200, {"buffered": len(BUFFER), "pending": len(PENDING)})
        else:
            self._send_json(404, {"error": "unknown path"})

    def do_POST(self) -> None:
        if self.path != "/readings":
            self._send_json(404, {"error": "unknown path"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            reading = json.loads(self.rfile.read(length))
            temperature = float(reading["temperature"])
        except (ValueError, KeyError, TypeError):
            self._send_json(400, {"error": "temperature is required"})
            return

        store_reading(temperature)
        self._send_json(200, {"temperature": temperature, "action": decide_action(temperature)})

    def _send_json(self, status: int, body: Any) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    print(f"edge node on http://localhost:{PORT}")
    HTTPServer(("localhost", PORT), EdgeHandler).serve_forever()


if __name__ == "__main__":
    main()
