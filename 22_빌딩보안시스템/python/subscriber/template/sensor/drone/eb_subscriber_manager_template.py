from common.eb_constants import EBConstants
from common.template.component_type import ComponentType
from subscriber.eb_abstract_subscriber_manager import EBAbstractSubscriberManager
from subscriber.template.sensor.observer_for_sensor import ObserverForSensor
from subscriber.template.sensor.sensor_subscriber import SensorSubscriber


class EBSubscriberManagerTemplate(EBAbstractSubscriberManager):
    """Subscriber 들 중 하나인 Drone Sensor 를 구동한다."""

    def init(self) -> None:
        drone_subscriber = SensorSubscriber(ComponentType.DRONE, None, EBConstants.RMI_PORT)
        observer_for_drone = ObserverForSensor(drone_subscriber.get_sensor_alarm(), drone_subscriber)

        self.add_user_subscriber(drone_subscriber)
        self.add_user_observer(observer_for_drone)
