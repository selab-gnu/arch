import threading
import time
from typing import Optional


class Slave(threading.Thread):
    """Master 대신 일부 작업을 수행하는 실행 단위(Active Object)."""

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name=name)
        self._done = False

    def halt(self) -> None:
        self._done = True

    def task(self) -> bool:
        """작업을 한 단계 수행한다. 목표에 도달하면 True.

        if state == goal: return True
        improve state
        return False
        """
        return True  # 지금은 바로 끝남

    def run(self) -> None:
        while not self._done:
            self._done = self.task()
            # 다른 스레드에 양보 (1초 대기)
            time.sleep(1)
