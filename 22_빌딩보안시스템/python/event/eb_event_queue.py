from typing import Any, Dict, List, Optional

from event.eb_event import EBEvent


class EBEventQueue:
    """이벤트를 저장하는 큐.

    등록된 Subscriber 는 각각 큐를 가지고, 주기적으로 회수하여 자신에게 전송된 이벤트를 확인한다.
    Event Bus Server 는 전송되는 이벤트를 모든 큐에 삽입한다.
    """

    def __init__(self) -> None:
        self._event_queue: List[EBEvent] = []
        self._component_id = 0

    def add_event(self, event: EBEvent) -> None:
        self._event_queue.append(event)

    def get_event(self) -> Optional[EBEvent]:
        """저장된 첫 번째 이벤트를 FIFO 로 꺼낸다. 비어 있으면 None."""
        if self._event_queue:
            return self._event_queue.pop(0)
        return None

    def clone_this_queue(self) -> "EBEventQueue":
        """회수를 위해 큐를 복제해서 돌려주고, 자신은 비운다."""
        new_queue = EBEventQueue()
        new_queue.set_queue_id(self._component_id)
        new_queue._event_queue = list(self._event_queue)
        self._event_queue.clear()
        return new_queue

    def get_size(self) -> int:
        return len(self._event_queue)

    def get_queue_id(self) -> int:
        return self._component_id

    def set_queue_id(self, component_id: int) -> None:
        self._component_id = component_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self._component_id,
            "events": [event.to_dict() for event in self._event_queue],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EBEventQueue":
        queue = EBEventQueue()
        queue.set_queue_id(data["component_id"])
        for event in data["events"]:
            queue.add_event(EBEvent.from_dict(event))
        return queue
