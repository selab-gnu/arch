"""Java RMI 의 LocateRegistry / Registry 역할을 하는 작은 브로커. (04rmi 실습의 naming.py 와 같은 구조)

Python 에는 Java RMI 가 없으므로 표준 라이브러리 xmlrpc 를 사용한다.
프록시에서 메서드를 호출하면 "Name.method" 라는 이름의 XML-RPC 요청이 전송되고,
레지스트리가 이름으로 객체를 찾아 메서드를 실행한 뒤 결과를 돌려준다.
"""
from socketserver import ThreadingMixIn
from typing import Any, Dict
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer


class _ThreadedServer(ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True


class Registry:
    def __init__(self, port: int) -> None:
        self._objects: Dict[str, Any] = {}
        self._server = _ThreadedServer(("127.0.0.1", port), logRequests=False, allow_none=True)
        self._server.register_instance(self)

    def bind(self, name: str, obj: Any) -> None:
        self._objects[name] = obj

    def serve_forever(self) -> None:
        self._server.serve_forever()

    # xmlrpc 서버가 모든 요청을 이 메서드로 넘긴다. method 예: "Event_Bus.register"
    def _dispatch(self, method: str, params: tuple) -> Any:
        name, _, meth = method.partition(".")
        obj = self._objects.get(name)
        if obj is None:
            raise LookupError(f"NotBoundException: {name}")
        if not meth or meth.startswith("_"):
            raise AttributeError(f"cannot call '{meth}'")
        return getattr(obj, meth)(*params)


def create_registry(port: int) -> Registry:
    """Java 의 LocateRegistry.createRegistry(port). 포트가 이미 사용 중이면 OSError."""
    return Registry(port)


def lookup(host: str, port: int, name: str) -> Any:
    """Java 의 Registry.lookup(name). 원격 객체의 프록시를 돌려준다.

    ServerProxy 는 스레드 안전하지 않으므로 호출할 때마다 새로 만들어 쓴다.
    """
    if host == "localhost":
        # macOS 등에서는 localhost 가 IPv6(::1) 로 먼저 풀릴 수 있다. 서버는 IPv4 로 열려 있으므로 맞춰 준다.
        host = "127.0.0.1"
    return getattr(ServerProxy(f"http://{host}:{port}/", allow_none=True), name)
