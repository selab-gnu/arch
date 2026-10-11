from typing import List

from slave import Slave


class Master:
    """작업을 여러 Slave 에 나누어 맡기고, Slave 가 모두 끝나기를 기다린다."""

    def __init__(self, slave_count: int = 10) -> None:
        self.slave_count = slave_count
        self.slaves: List[Slave] = []

    def run(self) -> None:
        # Slave 생성
        self.slaves = [Slave(name=f"Thread-{i}") for i in range(self.slave_count)]
        # Slave 시작
        for slave in self.slaves:
            slave.start()
        # Slave 가 끝나기를 기다림
        for slave in self.slaves:
            slave.join()
            print(f"{slave.name} has died")
        print("The master will now die ... ")
