from typing import Optional

from blackboard.framework.black_board import BlackBoard
from blackboard.framework.black_board_object import BlackBoardObject
from blackboard.framework.knowledge_source import KnowledgeSource


class AbstractKnowledgeSource(KnowledgeSource):
    def __init__(self) -> None:
        self._bbo: Optional[BlackBoardObject] = None
        self._bb: Optional[BlackBoard] = None

    def run(self) -> None:
        self.update_black_board_object(self.process(self._bbo))

    def update_black_board_object(self, bbo: BlackBoardObject) -> None:
        self._bb.add_black_board_object(bbo)
