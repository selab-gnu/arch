from typing import Optional

from common.eb_observer import EBObserver
from common.template.constants import Constants
from event.eb_event import EBEvent
from event.template.notification_event import NotificationEvent
from event.template.notification_event_id import NotificationEventID
from subscriber.eb_abstract_subscriber import EBAbstractSubscriber
from subscriber.template.sensor.gui.sensor_alarm import SensorAlarm


class ObserverForSensor(EBObserver):
    """각 Sensor 에서의 원격 호출을 기록한다."""

    def __init__(self, sensor_alarm: SensorAlarm, subscriber: Optional[EBAbstractSubscriber] = None) -> None:
        self._sensor_alarm = sensor_alarm
        self._subscriber = subscriber

    def notify_registration(self, component_id: int) -> None:
        self._sensor_alarm.print_message(f"{Constants.REGISTRATION}{component_id}")

    def notify_unregistration(self, component_id: int) -> None:
        self._sensor_alarm.print_message(f"{Constants.UNREGISTRATION}{component_id}")
        if self._subscriber is not None:
            self._subscriber.send_event(NotificationEvent(NotificationEventID.UNREGISTRATION, component_id))

    def notify_sending_an_event(self, event: EBEvent) -> None:
        if isinstance(event, NotificationEvent):
            if event.get_message() == NotificationEventID.TRESPASSING:
                self._sensor_alarm.print_message(f"{Constants.EVENTSENT}{Constants.TRESPASSING}")
            elif event.get_message() == NotificationEventID.IDLE:
                self._sensor_alarm.print_message(f"{Constants.EVENTSENT}{Constants.IDLE}")

    def notify_getting_an_event_queue(self, component_id: int) -> None:
        pass
