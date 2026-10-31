"""주문 서비스. 주문 데이터를 소유하고, 상품 정보는 상품 서비스의 API 로 얻는다.

실행:  python order_service.py   (python/microservice 폴더에서)
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PORT = 5002
PRODUCT_SERVICE_URL = "http://localhost:5001"

# 이 서비스만 접근하는 자체 저장소
ORDERS: List[Dict[str, Any]] = []


class ProductServiceDown(Exception):
    """상품 서비스에 연결할 수 없을 때 발생한다."""


def fetch_product(product_id: int) -> Optional[Dict[str, Any]]:
    """상품 서비스를 HTTP 로 호출한다. 상품이 없으면 None."""
    try:
        with urlopen(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=3) as response:
            return json.load(response)
    except HTTPError as e:
        if e.code == 404:
            return None
        raise ProductServiceDown() from e
    except URLError as e:
        raise ProductServiceDown() from e


class OrderHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/orders":
            self._send_json(200, ORDERS)
        else:
            self._send_json(404, {"error": "unknown path"})

    def do_POST(self) -> None:
        if self.path != "/orders":
            self._send_json(404, {"error": "unknown path"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            request = json.loads(self.rfile.read(length))
            product_id = int(request["product_id"])
            quantity = int(request["quantity"])
        except (ValueError, KeyError, TypeError):
            self._send_json(400, {"error": "product_id and quantity are required"})
            return

        try:
            product = fetch_product(product_id)
        except ProductServiceDown:
            self._send_json(503, {"error": "product service unavailable"})
            return
        if product is None:
            self._send_json(404, {"error": "product not found"})
            return

        order = {
            "id": len(ORDERS) + 1,
            "product_id": product_id,
            "quantity": quantity,
            "total_price": product["price"] * quantity,
        }
        ORDERS.append(order)
        self._send_json(201, order)

    def _send_json(self, status: int, body: Any) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    print(f"order service on http://localhost:{PORT}")
    HTTPServer(("localhost", PORT), OrderHandler).serve_forever()


if __name__ == "__main__":
    main()
