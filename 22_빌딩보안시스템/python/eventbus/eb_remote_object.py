import itertools
import threading
from typing import Any, Dict, Optional

from common.eb_observer import EBObserver
from common.eb_rmi_interface import EBRMIInterface
from event.eb_event import EBEvent
from event.eb_event_queue import EBEventQueue


class EBRemoteObject(EBRMIInterface):
    """EBRMIInterface 를 구체화한 원격 객체. Java 의 synchronized 메서드는 Lock 으로 옮겼다."""

    def __init__(self, user_eb_observer: Optional[EBObserver] = None) -> None:
        self._event_queue_list: Dict[int, EBEventQueue] = {}
        self._eb_observer = user_eb_observer
        self._lock = threading.Lock()
        self._next_id = itertools.count(1)

    def register(self) -> int:
        with self._lock:
            new_queue = EBEventQueue()
            component_id = next(self._next_id)

            new_queue.set_queue_id(component_id)
            self._event_queue_list[component_id] = new_queue

            if self._eb_observer is not None:
                self._eb_observer.notify_registration(component_id)

            return component_id

    def un_register(self, component_id: int) -> bool:
        with self._lock:
            if component_id in self._event_queue_list:
                del self._event_queue_list[component_id]

                if self._eb_observer is not None:
                    self._eb_observer.notify_unregistration(component_id)

                return True
            return False

    def send_event(self, event: Dict[str, Any]) -> None:
        with self._lock:
            decoded_event = EBEvent.from_dict(event)
            for queue in self._event_queue_list.values():
                queue.add_event(decoded_event)

            if self._eb_observer is not None:
                self._eb_observer.notify_sending_an_event(decoded_event)

    def get_event_queue(self, component_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            if component_id in self._event_queue_list:
                cloned_event_queue = self._event_queue_list[component_id].clone_this_queue()

                if self._eb_observer is not None:
                    self._eb_observer.notify_getting_an_event_queue(component_id)
                return cloned_event_queue.to_dict()
            return None
