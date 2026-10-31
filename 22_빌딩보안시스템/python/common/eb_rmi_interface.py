from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class EBRMIInterface(ABC):
    """원격에서 호출되는 함수들을 정의한 인터페이스.

    XML-RPC 는 기본 자료형만 주고받을 수 있으므로 이벤트와 큐는 dict 로 변환해서 전달한다.
    """

    @abstractmethod
    def register(self) -> int:
        """Subscriber 를 등록하고 ID 를 돌려준다."""

    @abstractmethod
    def un_register(self, component_id: int) -> bool:
        """Subscriber 를 등록 해제한다."""

    @abstractmethod
    def send_event(self, event: Dict[str, Any]) -> None:
        """Event Bus 를 통해 이벤트 전송을 요청한다."""

    @abstractmethod
    def get_event_queue(self, component_id: int) -> Optional[Dict[str, Any]]:
        """이벤트를 받기 위해 자신의 큐를 회수한다."""
