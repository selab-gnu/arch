from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .black_board import BlackBoard
    from .control_data import ControlData


class KnowledgeWorker(ABC):
    """각 KnowledgeWorker 는 자신이 문제 해결에 기여할 수 있는 조건을 스스로 알고 있다."""

    def __init__(self, name: str, blackboard: Optional[BlackBoard] = None) -> None:
        self._can_contribute = False
        self._name = name
        self.blackboard = blackboard
        self._keys: Dict[str, ControlData] = {}

    def get_name(self) -> str:
        return self._name

    @abstractmethod
    def execute_action(self) -> None:
        ...

    @abstractmethod
    def execute_condition(self) -> None:
        ...

    @abstractmethod
    def update_blackboard(self) -> None:
        ...
