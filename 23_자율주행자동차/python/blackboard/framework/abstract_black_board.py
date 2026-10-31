from typing import List

from blackboard.framework.black_board import BlackBoard
from blackboard.framework.black_board_controller import BlackBoardController
from blackboard.framework.black_board_object import BlackBoardObject


class AbstractBlackBoard(BlackBoard):
    """BlackBoardObject 를 받으면 관찰자인 Controller 에게 알린다."""

    def __init__(self) -> None:
        self._observers: List[BlackBoardController] = []

    def add_observer(self, observer: BlackBoardController) -> None:
        self._observers.append(observer)

    def add_black_board_object(self, bbo: BlackBoardObject) -> None:
        self.notify_controller(bbo)

    def notify_controller(self, bbo: BlackBoardObject) -> None:
        for observer in self._observers:
            observer.update(self, bbo)
