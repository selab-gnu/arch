from __future__ import annotations

from typing import TYPE_CHECKING

from .publisher import Publisher

if TYPE_CHECKING:
    from pubsub.message import Message
    from pubsub.service.pub_sub_service import PubSubService


class PublisherImpl(Publisher):
    def publish(self, message: Message, pub_sub_service: PubSubService) -> None:
        # 게시자는 구독자를 알지 못한다. 서비스의 큐에 메시지를 넣을 뿐이다.
        pub_sub_service.add_message_to_queue(message)
