from common.eb_observer import EBObserver
from common.template.component_type import ComponentType
from common.template.constants import Constants
from event.eb_event import EBEvent
from event.template.command_event import CommandEvent
from event.template.command_event_id import CommandEventID
from event.template.notification_event import NotificationEvent
from event.template.notification_event_id import NotificationEventID
from event.template.registration_event import RegistrationEvent
from eventbus.template.gui.event_bus_monitor import EventBusMonitor


class ObserverForEventBus(EBObserver):
    """Event Bus Server 에서의 원격 호출을 EventBusMonitor 에 기록한다."""

    def __init__(self, monitor_window: EventBusMonitor) -> None:
        self._monitor_window = monitor_window

    def notify_registration(self, component_id: int) -> None:
        self._monitor_window.print_message(f"{Constants.REGISTRATION}{component_id}")

    def notify_unregistration(self, component_id: int) -> None:
        self._monitor_window.print_message(f"{Constants.UNREGISTRATION}{component_id}")

    def notify_sending_an_event(self, event: EBEvent) -> None:
        if isinstance(event, CommandEvent):
            command_event_id: CommandEventID = event.get_message()
            self._monitor_window.print_message(
                f"{Constants.EVENTSENT}{event.get_related_component_id()}({command_event_id.name})")
        elif isinstance(event, NotificationEvent):
            notification_event_id: NotificationEventID = event.get_message()
            self._monitor_window.print_message(
                f"{Constants.EVENTSENT}{event.get_related_component_id()}({notification_event_id.name})")
        elif isinstance(event, RegistrationEvent):
            component_type: ComponentType = event.get_message()
            self._monitor_window.print_message(
                f"{Constants.EVENTSENT}(등록 알람){event.get_related_component_id()}"
                f"({component_type.get_string_value()})")

    def notify_getting_an_event_queue(self, component_id: int) -> None:
        pass
