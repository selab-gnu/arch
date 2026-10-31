from eventbus.eb_abstract_manager import EBAbstractManager
from eventbus.template.gui.event_bus_monitor import EventBusMonitor
from eventbus.template.observer_for_event_bus import ObserverForEventBus


class EBManagerTemplate(EBAbstractManager):
    """사용자가 Event Bus 와 함께 구동하고자 하는 기능을 호출한다. eb_server_main 이 초기에 호출한다."""

    def init(self) -> None:
        # 사용자 정의 Observer 가 있다면 add_custom_observer 로 등록한다
        self.add_custom_observer(ObserverForEventBus(EventBusMonitor()))
