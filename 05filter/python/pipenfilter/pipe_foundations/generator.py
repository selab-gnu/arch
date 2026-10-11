from abc import abstractmethod
from typing import Generic, TypeVar

from .pipe import Pipe
from .threaded_runner import ThreadedRunner

T = TypeVar("T")


class Generator(ThreadedRunner, Generic[T]):
    """데이터를 만들어 파이프로 내보내는 시작점(source)."""

    def __init__(self, output: Pipe[T]) -> None:
        super().__init__()
        self.output = output

    def run(self) -> None:
        self.generate_into(self.output)

    @abstractmethod
    def generate_into(self, pipe: Pipe[T]) -> None:
        ...
