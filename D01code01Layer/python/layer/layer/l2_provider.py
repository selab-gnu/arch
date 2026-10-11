from abc import ABC, abstractmethod
from typing import Optional

from .l1_provider import L1Provider


class L2Provider(ABC):
    """2계층 추상 레이어. 바로 아래의 L1Provider만 사용할 수 있다."""

    def __init__(self) -> None:
        self.level1: Optional[L1Provider] = None

    @abstractmethod
    def l2_service(self) -> None:
        ...

    def set_lower_layer(self, level1: L1Provider) -> None:
        self.level1 = level1
