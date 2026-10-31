from blackboard.framework.abstract_black_board_controller import AbstractBlackBoardController
from blackboard.framework.black_board_object import BlackBoardObject


class AutoNavBBController(AbstractBlackBoardController):
    """Blackboard 에 BlackBoardObject 가 추가되면 알림을 받는다."""

    def exec_outcome(self, bbo: BlackBoardObject) -> None:
        print("==>> Operating brake pedal")
