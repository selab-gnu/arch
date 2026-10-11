from abc import ABC, abstractmethod


class Service(ABC):
    """서버가 제공하는 서비스의 공통 인터페이스."""

    @abstractmethod
    def run_service(self) -> None:
        ...
