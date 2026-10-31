from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional


class ControlData:
    """칠판에 기록되는 한 건의 데이터. Control 은 이 정보를 보고 다음 KnowledgeWorker 를 정한다."""

    def __init__(self, problem: Optional[str] = None, input_data: Optional[List[Any]] = None) -> None:
        self.problem = problem
        self.input = input_data
        self.output: Optional[List[Any]] = None
        self.updateby: Optional[str] = None
        self.updated: Optional[datetime] = datetime.now() if problem is not None else None

    def get_result(self) -> Optional[List[Any]]:
        return self.output

    def clone(self) -> ControlData:
        clone = ControlData(self.problem, self.input)
        clone.updated = self.updated
        clone.updateby = self.updateby
        clone.output = self.output
        return clone
