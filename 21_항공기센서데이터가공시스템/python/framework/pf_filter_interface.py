from abc import ABC, abstractmethod

from .piped_stream import PipedInputStream, PipedOutputStream


class PFFilterInterface(ABC):
    """PFGeneralFilter 의 기본 public 메서드를 정의한 인터페이스."""

    @abstractmethod
    def connect(self, index_for_output_port_in_this_filter: int,
                connected_input_port_in_next_filter: PipedInputStream) -> None:
        """두 필터를 연결한다. 이 필터의 출력 포트(index)를 다음 필터의 입력 포트에 연결."""

    @abstractmethod
    def get_input_port(self, index: int) -> PipedInputStream:
        """index 에 해당하는 입력 포트를 돌려준다."""

    @abstractmethod
    def get_output_port(self, index: int) -> PipedOutputStream:
        """index 에 해당하는 출력 포트를 돌려준다."""
