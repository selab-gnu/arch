import atexit
from typing import Optional

from common.template.component_type import ComponentType
from event.eb_event import EBEvent
from event.template.command_event import CommandEvent
from event.template.command_event_id import CommandEventID
from subscriber.eb_abstract_subscriber import EBAbstractSubscriber
from subscriber.template.sensor.gui.sensor_alarm import SensorAlarm


class SensorSubscriber(EBAbstractSubscriber):
    """Sensor 컴포넌트가 Event Bus Server 와 소통하기 위한 클래스."""

    def __init__(self, component_type: ComponentType, registry_host: Optional[str], registry_port: int,
                 frequency_to_get_event_queue: int = 1000) -> None:
        super().__init__(registry_host, registry_port, frequency_to_get_event_queue)
        self._component_type = component_type
        self._sensor_alarm = SensorAlarm(
            component_type.get_string_value(), self.get_component_id(), component_type, self)
        # 갑작스럽게 종료될 때 등록 해제를 하고 종료한다 (Java 의 shutdown hook)
        atexit.register(self.unregister)

    def get_sensor_alarm(self) -> SensorAlarm:
        return self._sensor_alarm

    def get_component_type(self) -> ComponentType:
        return self._component_type

    def assign_work_for_an_event(self, event: EBEvent) -> None:
        if isinstance(event, CommandEvent):
            if event.get_related_component_id() == self.get_component_id():
                if event.get_message() == CommandEventID.TURNON:
                    self._sensor_alarm.turn_on_alarm()
                elif event.get_message() == CommandEventID.TURNOFF:
                    self._sensor_alarm.turn_off_alarm()
