from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Deque, Dict, Set

if TYPE_CHECKING:
    from pubsub.message import Message
    from pubsub.subscriber.subscriber import Subscriber


class PubSubService:
    """게시자와 구독자 사이를 중개하는 서비스(메시지 브로커)."""

    def __init__(self) -> None:
        # 주제별 구독자 집합 (set 으로 중복 방지)
        self.subscribers_topic_map: Dict[str, Set[Subscriber]] = {}
        # 게시자가 발행한 메시지를 보관하는 큐
        self.messages_queue: Deque[Message] = deque()

    def add_message_to_queue(self, message: Message) -> None:
        self.messages_queue.append(message)

    def add_subscriber(self, topic: str, subscriber: Subscriber) -> None:
        self.subscribers_topic_map.setdefault(topic, set()).add(subscriber)

    def remove_subscriber(self, topic: str, subscriber: Subscriber) -> None:
        if topic in self.subscribers_topic_map:
            self.subscribers_topic_map[topic].discard(subscriber)

    def broadcast(self) -> None:
        """큐에 쌓인 메시지를 해당 주제의 모든 구독자에게 전달한다. 전달 후 큐는 비워진다."""
        if not self.messages_queue:
            print("No messages from publishers to display")
            return

        while self.messages_queue:
            message = self.messages_queue.popleft()
            # 구독자가 없는 주제의 메시지는 버려진다 (Java 버전은 이 경우 NullPointerException)
            for subscriber in self.subscribers_topic_map.get(message.topic, set()):
                subscriber.subscriber_messages.append(message)

    def get_messages_for_subscriber_of_topic(self, topic: str, subscriber: Subscriber) -> None:
        """특정 구독자가 특정 주제의 메시지를 요청할 때 전달한다."""
        if not self.messages_queue:
            print("No messages from publishers to display")
            return

        while self.messages_queue:
            message = self.messages_queue.popleft()
            if message.topic.lower() == topic.lower():
                if subscriber in self.subscribers_topic_map.get(topic, set()):
                    subscriber.subscriber_messages.append(message)
