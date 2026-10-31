from abc import ABC, abstractmethod

from event.eb_event import EBEvent


class EBObserver(ABC):
    """EBRMIInterface 에 정의된 원격 호출을 기록하는 인터페이스. 사용자 정의 Observer 가 상속해서 작성한다."""

    @abstractmethod
    def notify_registration(self, component_id: int) -> None:
        ...

    @abstractmethod
    def notify_unregistration(self, component_id: int) -> None:
        ...

    @abstractmethod
    def notify_sending_an_event(self, event: EBEvent) -> None:
        ...

    @abstractmethod
    def notify_getting_an_event_queue(self, component_id: int) -> None:
        ...
