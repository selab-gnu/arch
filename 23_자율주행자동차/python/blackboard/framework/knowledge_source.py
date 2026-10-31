from abc import ABC, abstractmethod

from blackboard.framework.black_board import BlackBoard
from blackboard.framework.black_board_object import BlackBoardObject


class KnowledgeSource(ABC):
    """BlackBoardObject 를 처리해서 새로운 BlackBoardObject 를 만든다."""

    @abstractmethod
    def run(self) -> None:
        ...

    @abstractmethod
    def is_interested(self, bbo: BlackBoardObject, bb: BlackBoard) -> bool:
        ...

    @abstractmethod
    def process(self, bbo: BlackBoardObject) -> BlackBoardObject:
        ...

    @abstractmethod
    def update_black_board_object(self, bbo: BlackBoardObject) -> None:
        ...
