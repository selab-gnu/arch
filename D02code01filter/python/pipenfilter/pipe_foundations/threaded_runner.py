import threading
import time
from abc import ABC, abstractmethod


class ThreadedRunner(ABC):
    """각 컴포넌트(생성기, 필터, 싱크)를 별도 스레드에서 실행한다."""

    def __init__(self) -> None:
        self._is_started = False
        self._thread = None

    @abstractmethod
    def run(self) -> None:
        ...

    def start(self) -> None:
        if not self._is_started:
            self._is_started = True
            self._thread = threading.Thread(target=self.run, name=type(self).__name__)
            self._thread.start()

    def stop(self) -> None:
        self._is_started = False

    def join(self) -> None:
        if self._thread is not None:
            self._thread.join()

    def delay_for_debug(self, millis: int) -> None:
        """다른 스레드가 동시에 도는 것을 눈으로 확인하기 위한 지연 (디버깅용)."""
        time.sleep(millis / 1000)
