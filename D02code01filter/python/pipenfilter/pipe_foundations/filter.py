from abc import abstractmethod
from typing import Generic, TypeVar

from .pipe import Pipe
from .threaded_runner import ThreadedRunner

I = TypeVar("I")
O = TypeVar("O")


class Filter(ThreadedRunner, Generic[I, O]):
    """입력 파이프에서 읽어 변환한 뒤 출력 파이프로 내보내는 필터."""

    def __init__(self, input: Pipe[I], output: Pipe[O]) -> None:
        super().__init__()
        self.input = input
        self.output = output

    def run(self) -> None:
        self.transform_between(self.input, self.output)

    @abstractmethod
    def transform_between(self, input: Pipe[I], output: Pipe[O]) -> None:
        ...
