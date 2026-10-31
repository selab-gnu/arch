import traceback
from abc import abstractmethod
from typing import List

from .pf_filter_interface import PFFilterInterface
from .piped_stream import PipedInputStream, PipedOutputStream


class EndOfStreamException(Exception):
    """필터 사이에 전달되는 데이터가 끝났음을 알리는 예외."""


class PFGeneralFilter(PFFilterInterface):
    """필터의 기본 메서드와 변수를 정의한 추상 클래스. 사용자 정의 필터는 이 클래스를 상속받아 구현한다."""

    def __init__(self, number_of_input_ports: int = 1, number_of_output_ports: int = 1) -> None:
        self.in_ports: List[PipedInputStream] = [PipedInputStream() for _ in range(number_of_input_ports)]
        self.out_ports: List[PipedOutputStream] = [PipedOutputStream() for _ in range(number_of_output_ports)]

    def _close_ports(self) -> None:
        """포트를 모두 닫는다. 출력 포트가 닫히면 다음 필터의 read() 가 -1 을 받는다."""
        for port in self.in_ports:
            port.close()
        for port in self.out_ports:
            port.close()

    def run(self) -> None:
        """스레드에서 실행되는 본체. EndOfStreamException 이 날 때까지 compute() 를 반복한다."""
        while True:
            try:
                self.compute()
            except EndOfStreamException:
                self._close_ports()
                return
            except Exception:
                traceback.print_exc()

    def connect(self, index_for_output_port_in_this_filter: int,
                connected_input_port_in_next_filter: PipedInputStream) -> None:
        self.out_ports[index_for_output_port_in_this_filter].connect(connected_input_port_in_next_filter)

    def get_input_port(self, index: int) -> PipedInputStream:
        return self.in_ports[index]

    def get_output_port(self, index: int) -> PipedOutputStream:
        return self.out_ports[index]

    def read_bytes(self, length: int, port: int = 0) -> bytes:
        """입력 포트에서 length 바이트를 읽는다. 중간에 스트림이 끝나면 EndOfStreamException."""
        data = bytearray()
        for _ in range(length):
            b = self.in_ports[port].read()
            if b == -1:
                raise EndOfStreamException()
            data.append(b)
        return bytes(data)

    @abstractmethod
    def compute(self) -> None:
        """필터에 계속 들어오는 데이터를 처리하는 반복 작업. 데이터가 끝나면 EndOfStreamException 을 던진다."""
