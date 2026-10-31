import atexit
from typing import Dict, Optional

from common.template.component_type import ComponentType
from event.eb_event import EBEvent
from event.template.notification_event import NotificationEvent
from event.template.notification_event_id import NotificationEventID
from event.template.registration_event import RegistrationEvent
from subscriber.eb_abstract_subscriber import EBAbstractSubscriber
from subscriber.template.control.gui.control_console import ControlConsole


class ControlConsoleSubscriber(EBAbstractSubscriber):
    """Control Console 컴포넌트가 Event Bus Server 와 소통하기 위한 클래스."""

    def __init__(self, registry_host: Optional[str], registry_port: int,
                 frequency_to_get_event_queue: int = 1000) -> None:
        super().__init__(registry_host, registry_port, frequency_to_get_event_queue)
        self._component_list: Dict[int, str] = {}
        self._console = ControlConsole(self)
        # 갑작스럽게 종료될 때 등록 해제를 하고 종료한다 (Java 의 shutdown hook)
        atexit.register(self.unregister)

    def assign_work_for_an_event(self, event: EBEvent) -> None:
        if isinstance(event, NotificationEvent):
            event_id = event.get_message()
            sender_id = event.get_related_component_id()

            if event_id == NotificationEventID.UNREGISTRATION:
                if sender_id in self._component_list:
                    del self._component_list[sender_id]
                    self._console.print_message(f"한 컴포넌트가 등록해제 되었습니다: {sender_id}")
                    self._console.unregister_sensor(sender_id)
                else:
                    self._console.print_message("해당 컴포넌트가 없습니다.")
            elif event_id == NotificationEventID.TRESPASSING:
                if sender_id in self._component_list:
                    self._console.print_message(f"컴포넌트에서 침입이 발생하였습니다!: {sender_id}")
                    self._console.turn_on_indicator(sender_id)
                else:
                    self._console.print_message("해당 컴포넌트가 없습니다.")
            elif event_id == NotificationEventID.IDLE:
                if sender_id in self._component_list:
                    self._console.print_message(f"컴포넌트가 안전한 상태입니다: {sender_id}")
                    self._console.turn_off_indicator(sender_id)
                else:
                    self._console.print_message("해당 컴포넌트가 없습니다.")
        elif isinstance(event, RegistrationEvent):
            component_type: ComponentType = event.get_message()
            component_id = event.get_related_component_id()

            self._component_list[component_id] = component_type.get_string_value()
            self._console.print_message(f"새로운 컴포넌트가 시스템에 등록되었습니다: {component_id}")
            self._console.add_new_sensor(component_type.get_string_value(), component_id)

    def get_console(self) -> ControlConsole:
        return self._console
