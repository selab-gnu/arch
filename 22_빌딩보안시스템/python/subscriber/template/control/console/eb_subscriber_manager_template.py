from common.eb_constants import EBConstants
from subscriber.eb_abstract_subscriber_manager import EBAbstractSubscriberManager
from subscriber.template.control.control_console_subscriber import ControlConsoleSubscriber
from subscriber.template.control.observer_for_control_console import ObserverForControlConsole


class EBSubscriberManagerTemplate(EBAbstractSubscriberManager):
    """Subscriber 들 중 하나인 Control Console 을 구동한다."""

    def init(self) -> None:
        control_console_subscriber = ControlConsoleSubscriber(None, EBConstants.RMI_PORT)
        observer_for_control_console = ObserverForControlConsole(control_console_subscriber.get_console())

        self.add_user_subscriber(control_console_subscriber)
        self.add_user_observer(observer_for_control_console)
