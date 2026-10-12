"""Java 의 java.io.PipedInputStream / PipedOutputStream 을 Python 으로 옮긴 것.

- 한 필터의 PipedOutputStream 을 다음 필터의 PipedInputStream 에 connect() 로 연결한다.
- 쓰는 쪽은 버퍼가 가득 차면 기다리고, 읽는 쪽은 버퍼가 비어 있으면 기다린다.
- 쓰는 쪽이 close() 하고 버퍼를 다 읽으면 read() 는 -1 을 돌려준다 (스트림 끝).
"""
import threading
from collections import deque
from typing import Deque, Optional

PIPE_SIZE = 1024  # Java PipedInputStream 기본 버퍼 크기


class PipedInputStream:
    def __init__(self, pipe_size: int = PIPE_SIZE) -> None:
        self._buffer: Deque[int] = deque()
        self._pipe_size = pipe_size
        self._cond = threading.Condition()
        self._writer_closed = False
        self._reader_closed = False
        self.connected = False

    def _receive(self, data: bytes) -> None:
        """PipedOutputStream 이 호출한다. 버퍼가 가득 차면 빈 공간이 생길 때까지 기다린다."""
        with self._cond:
            for b in data:
                while len(self._buffer) >= self._pipe_size:
                    if self._reader_closed:
                        raise IOError("Pipe closed")
                    self._cond.wait()
                self._buffer.append(b)
                self._cond.notify_all()

    def _receive_close(self) -> None:
        with self._cond:
            self._writer_closed = True
            self._cond.notify_all()

    def read(self) -> int:
        """1바이트를 읽어 0~255 정수로 돌려준다. 스트림이 끝났으면 -1."""
        with self._cond:
            while not self._buffer:
                if self._writer_closed or self._reader_closed:
                    return -1
                self._cond.wait()
            b = self._buffer.popleft()
            self._cond.notify_all()
            return b

    def close(self) -> None:
        with self._cond:
            self._reader_closed = True
            self._buffer.clear()
            self._cond.notify_all()


class PipedOutputStream:
    def __init__(self) -> None:
        self._sink: Optional[PipedInputStream] = None

    def connect(self, sink: PipedInputStream) -> None:
        if self._sink is not None or sink.connected:
            raise IOError("Already connected")
        self._sink = sink
        sink.connected = True

    def write(self, data) -> None:
        """int 하나(0~255) 또는 bytes 를 쓴다."""
        if self._sink is None:
            raise IOError("Pipe not connected")
        if isinstance(data, int):
            data = bytes([data & 0xFF])
        self._sink._receive(bytes(data))

    def close(self) -> None:
        if self._sink is not None:
            self._sink._receive_close()
