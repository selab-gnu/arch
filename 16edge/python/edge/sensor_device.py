"""온도 센서를 흉내 내어 측정값을 엣지 노드로 보내고, 결과를 확인한다.

실행:  python sensor_device.py   (두 서비스를 먼저 실행한 뒤, python/edge 폴더에서)
"""
import json
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EDGE_NODE_URL = "http://localhost:6002"
CLOUD_SERVICE_URL = "http://localhost:6001"

TEMPERATURES = [24.0, 25.5, 26.0, 31.5, 27.0, 26.5, 25.0, 33.0, 24.5, 26.0]


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
    for temperature in TEMPERATURES:
        call("POST", f"{EDGE_NODE_URL}/readings", {"temperature": temperature})
    call("GET", f"{EDGE_NODE_URL}/status")
    call("GET", f"{CLOUD_SERVICE_URL}/summaries")


if __name__ == "__main__":
    main()
