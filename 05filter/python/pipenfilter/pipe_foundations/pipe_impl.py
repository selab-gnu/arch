import threading
from collections import deque
from typing import Deque, Optional, TypeVar

from .pipe import Pipe

T = TypeVar("T")


class PipeImpl(Pipe[T]):
    """스레드 안전한 파이프. None 은 '파이프가 닫혔음'을 뜻하는 표시(sentinel)로 예약되어 있다."""

    def __init__(self) -> None:
        self._buffer: Deque[Optional[T]] = deque()
        self._is_open_for_writing = True
        self._has_read_last_object = False
        self._cond = threading.Condition()  # Java 의 synchronized + wait/notify

    def put(self, obj: T) -> bool:
        with self._cond:
            if not self._is_open_for_writing:
                raise IOError("pipe is closed; cannot write to it")
            if obj is None:
                raise ValueError("cannot put None in pipe; None is reserved for pipe-empty sentinel value")
            self._buffer.append(obj)
            self._cond.notify()
            return True

    def next_or_none_if_emptied(self) -> Optional[T]:
        with self._cond:
            if self._has_read_last_object:
                raise LookupError("pipe is closed and empty; will never contain any further values")
            while not self._buffer:
                self._cond.wait()  # 파이프가 비어 있으면 대기
            obj = self._buffer.popleft()
            if obj is None:  # 마지막 원소(닫힘 표시)
                self._has_read_last_object = True
            return obj

    def close_for_writing(self) -> None:
        with self._cond:
            self._is_open_for_writing = False
            self._buffer.append(None)
            self._cond.notify()
