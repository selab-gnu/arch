from abc import ABC, abstractmethod


class BlackBoardObject(ABC):
    """Blackboard 에 추가되는 데이터의 기본 단위.

    Knowledge Source 는 is_ready 플래그를 설정할 수 있다.
    Controller 는 이 값이 참이면 결정 단계를 실행한다.
    """

    @abstractmethod
    def is_ready(self) -> bool:
        ...
