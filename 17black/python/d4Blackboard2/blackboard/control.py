from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .black_board import BlackBoard


class Control:
    """칠판을 살펴보고 KnowledgeWorker 의 동작을 스케줄링한다."""

    def __init__(self, black_board: BlackBoard) -> None:
        self.black_board = black_board

    def loop(self) -> None:
        print("Starting loop")
        if self.black_board is None:
            raise Exception("blackboard is null")
        self.next_source()
        print("Loop ended")

    def next_source(self) -> None:
        """칠판을 살펴보고 다음에 수행할 지식원(KnowledgeWorker)을 선택한다."""
        # 칠판을 관찰한다 (worker 가 칠판에 항목을 추가해도 되도록 복사본을 순회)
        for value in list(self.black_board.inspect().values()):
            if value.problem == "PrimeNumbers":
                for worker in self.black_board.knowledge_workers:
                    if worker.get_name() == "PrimeFinder":
                        print("Knowledge Worker Found")
                        worker.execute_condition()
                        worker.execute_action()
                        worker.update_blackboard()
