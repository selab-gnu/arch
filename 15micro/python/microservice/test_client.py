"""두 서비스를 HTTP 로 호출해 보는 클라이언트.

실행:  python test_client.py   (두 서비스를 먼저 실행한 뒤, python/microservice 폴더에서)
"""
import json
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PRODUCT_SERVICE_URL = "http://localhost:5001"
ORDER_SERVICE_URL = "http://localhost:5002"


def call(method: str, url: str, body: Optional[Any] = None) -> None:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    print(f"{method} {url} {'' if body is None else json.dumps(body)}".rstrip())
    try:
        with urlopen(request, timeout=5) as response:
            print(f"  {response.status} {response.read().decode('utf-8')}")
    except HTTPError as e:
        print(f"  {e.code} {e.read().decode('utf-8')}")
    except URLError as e:
        print(f"  connection failed: {e.reason}")


def main() -> None:
    call("GET", f"{PRODUCT_SERVICE_URL}/products")
    call("POST", f"{ORDER_SERVICE_URL}/orders", {"product_id": 1, "quantity": 2})
    call("POST", f"{ORDER_SERVICE_URL}/orders", {"product_id": 99, "quantity": 1})
    call("GET", f"{ORDER_SERVICE_URL}/orders")


if __name__ == "__main__":
    main()
