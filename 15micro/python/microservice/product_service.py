"""상품 서비스. 상품 데이터를 소유하고 HTTP API 로만 공개한다.

실행:  python product_service.py   (python/microservice 폴더에서)
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

PORT = 5001

# 이 서비스만 접근하는 자체 저장소
PRODUCTS = {
    1: {"id": 1, "name": "keyboard", "price": 30000},
    2: {"id": 2, "name": "mouse", "price": 15000},
}


class ProductHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parts = self.path.strip("/").split("/")
        if parts == ["products"]:
            self._send_json(200, list(PRODUCTS.values()))
        elif len(parts) == 2 and parts[0] == "products" and parts[1].isdigit():
            product = PRODUCTS.get(int(parts[1]))
            if product is None:
                self._send_json(404, {"error": "product not found"})
            else:
                self._send_json(200, product)
        else:
            self._send_json(404, {"error": "unknown path"})

    def _send_json(self, status: int, body: Any) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    print(f"product service on http://localhost:{PORT}")
    HTTPServer(("localhost", PORT), ProductHandler).serve_forever()


if __name__ == "__main__":
    main()
