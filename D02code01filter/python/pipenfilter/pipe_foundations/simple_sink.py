from abc import abstractmethod
from typing import TypeVar

from .pipe import Pipe
from .sink import Sink

T = TypeVar("T")


class SimpleSink(Sink[T]):
    """값을 하나씩 handle 로 처리하는 싱크."""

    def take_from(self, pipe: Pipe[T]) -> None:
        try:
            while (item := pipe.next_or_none_if_emptied()) is not None:
                self.handle(item)
        finally:
            self.cleanup()

    @abstractmethod
    def handle(self, item: T) -> None:
        ...

    def cleanup(self) -> None:
        """파일 닫기 등 정리 작업이 필요하면 재정의한다."""
