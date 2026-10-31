from common.eb_observer import EBObserver
from common.template.constants import Constants
from event.eb_event import EBEvent
from event.template.command_event import CommandEvent
from event.template.command_event_id import CommandEventID
from event.template.notification_event import NotificationEvent
from event.template.notification_event_id import NotificationEventID
from subscriber.template.control.gui.control_console import ControlConsole


class ObserverForControlConsole(EBObserver):
    """Control Console 에서의 원격 호출을 기록한다."""

    def __init__(self, console: ControlConsole) -> None:
        self._console = console

    def notify_registration(self, component_id: int) -> None:
        self._console.print_message(f"{Constants.REGISTRATION}{component_id}")

    def notify_unregistration(self, component_id: int) -> None:
        self._console.print_message(f"{Constants.UNREGISTRATION}{component_id}")

    def notify_sending_an_event(self, event: EBEvent) -> None:
        if isinstance(event, NotificationEvent):
            if event.get_message() == NotificationEventID.TRESPASSING:
                self._console.print_message(f"{Constants.EVENTSENT}{Constants.TRESPASSING}")
            else:
                self._console.print_message(f"{Constants.EVENTSENT}{Constants.IDLE}")
        elif isinstance(event, CommandEvent):
            if event.get_message() == CommandEventID.TURNON:
                self._console.print_message(
                    f"{Constants.EVENTSENT}{event.get_related_component_id()}{Constants.TURNON_ALARM}")
            else:
                self._console.print_message(
                    f"{Constants.EVENTSENT}{event.get_related_component_id()}{Constants.TURNOFF_ALARM}")

    def notify_getting_an_event_queue(self, component_id: int) -> None:
        pass
