from abc import ABC, abstractmethod

from blackboard.framework.black_board_object import BlackBoardObject


class BlackBoard(ABC):
    """BlackBoardObject 를 받을 때마다 BlackBoardController 에 알린다."""

    @abstractmethod
    def add_black_board_object(self, bbo: BlackBoardObject) -> None:
        ...

    @abstractmethod
    def notify_controller(self, bbo: BlackBoardObject) -> None:
        ...
