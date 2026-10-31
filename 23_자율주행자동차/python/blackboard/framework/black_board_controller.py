from abc import ABC, abstractmethod
from typing import List

from blackboard.framework.black_board import BlackBoard
from blackboard.framework.black_board_object import BlackBoardObject
from blackboard.framework.knowledge_source import KnowledgeSource


class BlackBoardController(ABC):
    """Blackboard 를 관찰하다가 새로운 BlackBoardObject 가 들어오면 알림을 받는다."""

    @abstractmethod
    def update(self, bb: BlackBoard, bbo: BlackBoardObject) -> None:
        ...

    @abstractmethod
    def set_knowledge_source_list(self, ks_list: List[KnowledgeSource]) -> None:
        ...

    @abstractmethod
    def enroll_knowledge_source(self, ks: KnowledgeSource) -> None:
        ...

    @abstractmethod
    def exec_outcome(self, bbo: BlackBoardObject) -> None:
        ...
