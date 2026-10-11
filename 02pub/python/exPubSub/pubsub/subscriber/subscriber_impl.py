from __future__ import annotations

from typing import TYPE_CHECKING

from .subscriber import Subscriber

if TYPE_CHECKING:
    from pubsub.service.pub_sub_service import PubSubService


class SubscriberImpl(Subscriber):
    def add_subscriber(self, topic: str, pub_sub_service: PubSubService) -> None:
        pub_sub_service.add_subscriber(topic, self)

    def un_subscribe(self, topic: str, pub_sub_service: PubSubService) -> None:
        pub_sub_service.remove_subscriber(topic, self)

    def get_messages_for_subscriber_of_topic(self, topic: str, pub_sub_service: PubSubService) -> None:
        pub_sub_service.get_messages_for_subscriber_of_topic(topic, self)
