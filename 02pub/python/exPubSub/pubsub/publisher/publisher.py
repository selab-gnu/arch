from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pubsub.message import Message
    from pubsub.service.pub_sub_service import PubSubService


class Publisher(ABC):
    @abstractmethod
    def publish(self, message: Message, pub_sub_service: PubSubService) -> None:
        """새 메시지를 PubSubService 에 게시한다."""
