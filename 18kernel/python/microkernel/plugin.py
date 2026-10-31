from abc import ABC, abstractmethod


class Plugin(ABC):
    """모든 플러그인이 지켜야 하는 약속. 코어는 이 인터페이스만 안다."""

    name = ""

    @abstractmethod
    def execute(self, text: str) -> str:
        ...
