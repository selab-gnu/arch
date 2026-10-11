import random
from typing import Dict, List

from service import Service


class Dispatcher:
    """서비스 이름 → 실제 서버(서비스 객체) 목록을 관리하는 이름 서비스."""

    def __init__(self) -> None:
        self.registry: Dict[str, List[Service]] = {}
        self.rnd = random.Random(123456)  # Java 버전처럼 고정 시드 사용

    def register_service(self, svc: str, obj: Service) -> None:
        """서버가 자신의 서비스를 이름으로 등록한다."""
        self.registry.setdefault(svc, []).append(obj)

    def locate_server(self, svc: str) -> Service:
        """서비스 이름으로 서버를 찾아 돌려준다. 여러 개면 임의로 하나를 고른다."""
        servers = self.registry.get(svc)
        if not servers:
            raise LookupError(f"service '{svc}' is not registered")
        i = self.rnd.randrange(len(servers))
        return servers[i]
