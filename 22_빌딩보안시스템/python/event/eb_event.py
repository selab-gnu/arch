from typing import Any, Dict, Type

_EVENT_CLASSES: Dict[str, Type["EBEvent"]] = {}


class EBEvent:
    """Event Bus 에서 전송되는 이벤트.

    Java 는 객체 직렬화로 이벤트를 전송하지만, XML-RPC 는 dict 만 전달할 수 있다.
    하위 클래스는 자동으로 등록되고, to_dict / from_dict 로 변환된다.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        _EVENT_CLASSES[cls.__name__] = cls

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EBEvent":
        return _EVENT_CLASSES[data["event_class"]].decode(data)

    @classmethod
    def decode(cls, data: Dict[str, Any]) -> "EBEvent":
        raise NotImplementedError
