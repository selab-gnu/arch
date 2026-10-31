from blackboard.framework.abstract_black_board import AbstractBlackBoard
from blackboard.framework.black_board_object import BlackBoardObject


class AutoNavBlackBoard(AbstractBlackBoard):
    def add_black_board_object(self, bbo: BlackBoardObject) -> None:
        print(f"==>> Blackboard received BBO {type(bbo).__module__}.{type(bbo).__name__}")

        super().add_black_board_object(bbo)
