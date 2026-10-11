from abc import ABC, abstractmethod


class RmiServerIntf(ABC):
    """원격 객체의 인터페이스 (Java 의 RmiServerIntf extends Remote)."""

    @abstractmethod
    def get_message(self) -> str:
        ...
