from typing import Optional

from common.eb_observer import EBObserver


class EBAbstractManager:
    """Event Bus Server 를 구성하는 EBManagerTemplate 에서 사용할 수 있는 기본 함수."""

    def __init__(self) -> None:
        self.event_bus_ip_address: Optional[str] = None
        self.eb_observer: Optional[EBObserver] = None

    def set_event_bus_ip_address(self, event_bus_ip_address: str) -> None:
        self.event_bus_ip_address = event_bus_ip_address

    def get_user_observer(self) -> Optional[EBObserver]:
        return self.eb_observer

    def add_custom_observer(self, your_eb_observer: EBObserver) -> None:
        self.eb_observer = your_eb_observer
