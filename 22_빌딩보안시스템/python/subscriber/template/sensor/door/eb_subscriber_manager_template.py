from common.eb_constants import EBConstants
from common.template.component_type import ComponentType
from subscriber.eb_abstract_subscriber_manager import EBAbstractSubscriberManager
from subscriber.template.sensor.observer_for_sensor import ObserverForSensor
from subscriber.template.sensor.sensor_subscriber import SensorSubscriber


class EBSubscriberManagerTemplate(EBAbstractSubscriberManager):
    """Subscriber 들 중 하나인 Door Sensor 를 구동한다."""

    def init(self) -> None:
        door_subscriber = SensorSubscriber(ComponentType.DOOR, None, EBConstants.RMI_PORT)
        observer_for_door = ObserverForSensor(door_subscriber.get_sensor_alarm(), door_subscriber)

        self.add_user_subscriber(door_subscriber)
        self.add_user_observer(observer_for_door)
