from abc import ABC, abstractmethod
from typing import Optional

from .l2_provider import L2Provider


class L3Provider(ABC):
    """3계층 추상 레이어. 바로 아래의 L2Provider만 사용할 수 있다."""

    def __init__(self) -> None:
        self.level2: Optional[L2Provider] = None

    @abstractmethod
    def l3_service(self) -> None:
        ...

    def set_lower_layer(self, level2: L2Provider) -> None:
        self.level2 = level2
