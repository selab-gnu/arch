from typing import Any, Dict, List, Tuple

from .control import Control
from .control_data import ControlData
from .knowledge_worker import KnowledgeWorker


class BlackBoard:
    """중앙 데이터를 관리한다."""

    def __init__(self) -> None:
        self.knowledge_workers: List[KnowledgeWorker] = []
        self.control = Control(self)
        self._data: Dict[str, ControlData] = {}

    def add_knowledge_worker(self, new_knowledge_worker: KnowledgeWorker) -> None:
        new_knowledge_worker.blackboard = self
        self.knowledge_workers.append(new_knowledge_worker)

    def inspect(self) -> Dict[str, ControlData]:
        return self._data

    def update_entry(self, blackboard_entry: Tuple[str, ControlData]) -> None:
        key, value = blackboard_entry
        if key in self._data:
            self._data[key] = value
        else:
            raise Exception(f"{key} Not Found!")

    def update(self, key: str, data: ControlData) -> None:
        self._data[key] = data

    def print(self) -> None:
        print("Blackboard state")
        for key, cdata in self._data.items():
            print(f"data:{key}")
            print(f"\tProblem:{cdata.problem}")
            if cdata.input is not None:
                print(f"\tInput:{self._join(cdata.input)}")
            if cdata.output is not None:
                print(f"\tOutput:{self._join(cdata.output)}")

    def _join(self, values: List[Any]) -> str:
        return ", ".join(str(value) for value in values)
