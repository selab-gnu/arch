from typing import Optional

from common.eb_observer import EBObserver
from subscriber.eb_abstract_subscriber import EBAbstractSubscriber


class EBAbstractSubscriberManager:
    """Subscriber 를 구성하는 EBSubscriberManagerTemplate 에서 사용할 수 있는 기본 함수."""

    def __init__(self) -> None:
        self.subscriber: Optional[EBAbstractSubscriber] = None

    def add_user_subscriber(self, your_eb_abstract_subscriber: EBAbstractSubscriber) -> None:
        self.subscriber = your_eb_abstract_subscriber

    def add_user_observer(self, your_eb_observer: EBObserver) -> None:
        self.subscriber.set_user_eb_observer(your_eb_observer)
