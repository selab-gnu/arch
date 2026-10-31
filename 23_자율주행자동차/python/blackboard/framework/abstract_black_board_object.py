from blackboard.framework.black_board_object import BlackBoardObject


class AbstractBlackBoardObject(BlackBoardObject):
    def __init__(self) -> None:
        self._is_ready = False

    def is_ready(self) -> bool:
        return self._is_ready

    def set_ready(self, is_ready: bool) -> None:
        self._is_ready = is_ready
