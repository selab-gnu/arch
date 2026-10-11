from abc import ABC, abstractmethod


class L1Provider(ABC):
    """최하위(1계층) 추상 레이어. 하위 레이어가 없다."""

    @abstractmethod
    def l1_service(self) -> None:
        ...
