from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class Pipe(ABC, Generic[T]):
    """필터와 필터를 잇는 파이프의 인터페이스."""

    @abstractmethod
    def put(self, obj: T) -> bool:
        ...

    @abstractmethod
    def next_or_none_if_emptied(self) -> Optional[T]:
        """다음 값을 꺼낸다. 비어 있으면 기다린다. 파이프가 닫히고 모두 읽었으면 None."""

    @abstractmethod
    def close_for_writing(self) -> None:
        ...
