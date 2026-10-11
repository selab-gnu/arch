from abc import abstractmethod
from typing import Generic, TypeVar

from .pipe import Pipe
from .threaded_runner import ThreadedRunner

T = TypeVar("T")


class Sink(ThreadedRunner, Generic[T]):
    """파이프라인의 끝(sink). 최종 결과를 소비한다."""

    def __init__(self, input: Pipe[T]) -> None:
        super().__init__()
        self.input = input

    def run(self) -> None:
        self.take_from(self.input)

    @abstractmethod
    def take_from(self, pipe: Pipe[T]) -> None:
        ...
