"""Java RMI 의 LocateRegistry / Naming 역할을 흉내 낸 작은 브로커.

Python 에는 Java RMI 가 없으므로 표준 라이브러리 xmlrpc 를 사용한다.
- 서버 쪽: create_registry(port) 로 레지스트리(브로커)를 만들고, rebind(name, obj) 로 원격 객체를 등록한다.
- 클라이언트 쪽: lookup("//host:port/Name") 으로 원격 객체의 프록시(stub)를 얻는다.
프록시에서 메서드를 호출하면 "Name.method" 라는 이름의 XML-RPC 요청이 네트워크로 전송되고,
레지스트리가 이름으로 객체를 찾아 메서드를 실행한 뒤 결과를 돌려준다.
"""
from typing import Any, Dict
from urllib.parse import urlparse
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

DEFAULT_PORT = 1099  # Java RMI 레지스트리 기본 포트


class Registry:
    def __init__(self, port: int = DEFAULT_PORT) -> None:
        self._objects: Dict[str, Any] = {}
        self._server = SimpleXMLRPCServer(("127.0.0.1", port), logRequests=False, allow_none=True)
        self._server.register_instance(self)

    def rebind(self, name: str, obj: Any) -> None:
        """이름에 원격 객체를 등록한다. 같은 이름이 있으면 덮어쓴다."""
        self._objects[name] = obj

    def unbind(self, name: str) -> None:
        self._objects.pop(name, None)

    def serve_forever(self) -> None:
        self._server.serve_forever()

    # xmlrpc 서버가 모든 요청을 이 메서드로 넘긴다. method 예: "RmiServer.get_message"
    def _dispatch(self, method: str, params: tuple) -> Any:
        name, _, meth = method.partition(".")
        obj = self._objects.get(name)
        if obj is None:
            raise LookupError(f"NotBoundException: {name}")
        if not meth or meth.startswith("_"):
            raise AttributeError(f"cannot call '{meth}'")
        return getattr(obj, meth)(*params)


def create_registry(port: int = DEFAULT_PORT) -> Registry:
    """Java 의 LocateRegistry.createRegistry(port). 포트가 이미 사용 중이면 OSError."""
    return Registry(port)


def lookup(url: str) -> Any:
    """Java 의 Naming.lookup("//localhost/RmiServer"). 원격 객체의 프록시를 돌려준다."""
    parsed = urlparse(url if "://" in url else "rmi:" + url)
    host = parsed.hostname or "localhost"
    if host == "localhost":
        # macOS 등에서는 localhost 가 IPv6(::1) 로 먼저 풀릴 수 있다. 서버는 IPv4 로 열려 있으므로 맞춰 준다.
        host = "127.0.0.1"
    port = parsed.port or DEFAULT_PORT
    name = parsed.path.lstrip("/")
    proxy = ServerProxy(f"http://{host}:{port}/", allow_none=True)
    return getattr(proxy, name)
