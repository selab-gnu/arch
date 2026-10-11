from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from pubsub.message import Message
    from pubsub.service.pub_sub_service import PubSubService


class Subscriber(ABC):
    def __init__(self) -> None:
        # 구독자가 받은 모든 메시지를 저장
        self.subscriber_messages: List[Message] = []

    @abstractmethod
    def add_subscriber(self, topic: str, pub_sub_service: PubSubService) -> None:
        """PubSubService 에 특정 주제(topic)의 구독자로 등록한다."""

    @abstractmethod
    def un_subscribe(self, topic: str, pub_sub_service: PubSubService) -> None:
        """특정 주제의 구독을 취소한다."""

    @abstractmethod
    def get_messages_for_subscriber_of_topic(self, topic: str, pub_sub_service: PubSubService) -> None:
        """특정 주제의 메시지를 직접 요청한다."""

    def print_messages(self) -> None:
        for message in self.subscriber_messages:
            print(f"Message Topic -> {message.topic} : {message.payload}")
