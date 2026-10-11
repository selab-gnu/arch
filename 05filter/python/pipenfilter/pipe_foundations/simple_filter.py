from abc import abstractmethod
from typing import TypeVar

from .filter import Filter
from .pipe import Pipe

I = TypeVar("I")
O = TypeVar("O")


class SimpleFilter(Filter[I, O]):
    """값 하나를 받아 값 하나로 바꾸는 필터. transform_one 만 구현하면 된다."""

    def transform_between(self, input: Pipe[I], output: Pipe[O]) -> None:
        while (item := input.next_or_none_if_emptied()) is not None:
            output.put(self.transform_one(item))
        output.close_for_writing()

    @abstractmethod
    def transform_one(self, item: I) -> O:
        ...
