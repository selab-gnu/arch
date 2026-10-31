import threading
from typing import List

from blackboard.framework.black_board import BlackBoard
from blackboard.framework.black_board_controller import BlackBoardController
from blackboard.framework.black_board_object import BlackBoardObject
from blackboard.framework.knowledge_source import KnowledgeSource


class AbstractBlackBoardController(BlackBoardController):
    def __init__(self) -> None:
        self._ks_list: List[KnowledgeSource] = []

    def update(self, bb: BlackBoard, bbo: BlackBoardObject) -> None:
        if bbo.is_ready():
            self.exec_outcome(bbo)
        else:
            for ks in self._ks_list:
                if ks.is_interested(bbo, bb):
                    self.enroll_knowledge_source(ks)
                    break

    def set_knowledge_source_list(self, ks_list: List[KnowledgeSource]) -> None:
        self._ks_list = ks_list

    def enroll_knowledge_source(self, ks: KnowledgeSource) -> None:
        # main 이 끝난 뒤에도 Knowledge Source 가 다음 Knowledge Source 를 실행하므로
        # 인터프리터 종료 중에는 작업을 받지 않는 ThreadPoolExecutor 대신 Thread 를 사용한다
        threading.Thread(target=ks.run).start()
