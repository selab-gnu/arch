import threading
import time
import traceback
import xmlrpc.client
from abc import ABC, abstractmethod
from typing import Any, Optional

from common.eb_constants import EBConstants
from common.eb_observer import EBObserver
from common.naming import lookup
from event.eb_event import EBEvent
from event.eb_event_queue import EBEventQueue

_REMOTE_ERRORS = (OSError, xmlrpc.client.Error)  # Java 의 RemoteException 에 해당


class EBAbstractSubscriber(ABC):
    """Event Bus Server 에 등록하여 이벤트를 전송하고 큐를 회수하는 추상 클래스.

    큐 회수는 독립적인 스레드로 동작한다. 받은 이벤트에 대한 행동은 assign_work_for_an_event 에 작성한다.
    """

    def __init__(self, registry_host: Optional[str], registry_port: int,
                 frequency_to_get_event_queue: int = 1000) -> None:
        self._component_id = -1
        self._eb_observer: Optional[EBObserver] = None
        self._frequency_to_get_event_queue = frequency_to_get_event_queue  # milisecond
        self._registry_host = registry_host or "localhost"
        self._registry_port = registry_port

    def _rmi_inf(self) -> Any:
        return lookup(self._registry_host, self._registry_port, EBConstants.RMI_ID)

    def _get_event_queue(self) -> Optional[EBEventQueue]:
        event_queue = None
        if self._component_id != -1:
            try:
                data = self._rmi_inf().get_event_queue(self._component_id)
                if data is not None:
                    event_queue = EBEventQueue.from_dict(data)
            except _REMOTE_ERRORS:
                traceback.print_exc()

        if self._eb_observer is not None:
            self._eb_observer.notify_getting_an_event_queue(self._component_id)
        return event_queue

    def register(self) -> int:
        """Event Bus Server 에 등록을 요청하고, 성공하면 ID 를 돌려준다."""
        try:
            self._component_id = self._rmi_inf().register()
            threading.Thread(target=self.run, daemon=True).start()

            if self._eb_observer is not None:
                self._eb_observer.notify_registration(self._component_id)
        except _REMOTE_ERRORS:
            traceback.print_exc()
        return self._component_id

    def unregister(self) -> None:
        if self._component_id != -1:
            try:
                self._rmi_inf().un_register(self._component_id)

                if self._eb_observer is not None:
                    self._eb_observer.notify_unregistration(self._component_id)

                self._component_id = -1
            except _REMOTE_ERRORS:
                traceback.print_exc()

    def send_event(self, event: EBEvent) -> None:
        if self._component_id != -1:
            try:
                self._rmi_inf().send_event(event.to_dict())

                if self._eb_observer is not None:
                    self._eb_observer.notify_sending_an_event(event)
            except _REMOTE_ERRORS:
                traceback.print_exc()

    def get_component_id(self) -> int:
        return self._component_id

    def set_user_eb_observer(self, eb_observer: EBObserver) -> None:
        self._eb_observer = eb_observer

    def run(self) -> None:
        while self._component_id != -1:
            event_queue = self._get_event_queue()
            if event_queue is None:  # 등록 해제되었거나 서버에 연결할 수 없음
                break
            while event_queue.get_size() != 0:
                self.assign_work_for_an_event(event_queue.get_event())

            time.sleep(self._frequency_to_get_event_queue / 1000)

    @abstractmethod
    def assign_work_for_an_event(self, event: EBEvent) -> None:
        """전송된 이벤트마다 어떤 작업을 할 것인지 정의한다."""
