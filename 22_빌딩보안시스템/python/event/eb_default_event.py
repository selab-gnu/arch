from enum import Enum
from typing import Any, Dict, Optional, Type

from event.eb_event import EBEvent


class EBDefaultEvent(EBEvent):
    """이벤트 메시지와, 이벤트와 관련이 있는 Subscriber 의 ID 를 담는 기본 이벤트."""

    message_type: Optional[Type[Enum]] = None  # 메시지가 enum 이면 이름으로 전송한다

    def __init__(self, message: Any, component_id: Optional[int] = None) -> None:
        self._message = message
        self._related_component_id = component_id

    def get_message(self) -> Any:
        return self._message

    def get_related_component_id(self) -> Optional[int]:
        return self._related_component_id

    def set_related_component_id(self, component_id: int) -> None:
        self._related_component_id = component_id

    def to_dict(self) -> Dict[str, Any]:
        message = self._message.name if self.message_type else self._message
        return {
            "event_class": type(self).__name__,
            "message": message,
            "related_component_id": self._related_component_id,
        }

    @classmethod
    def decode(cls, data: Dict[str, Any]) -> EBEvent:
        message = cls.message_type[data["message"]] if cls.message_type else data["message"]
        return cls(message, data["related_component_id"])
