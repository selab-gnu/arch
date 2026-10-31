from blackboard.autonav.bbo.brake_pedal_bbo import BrakePedalBBO
from blackboard.autonav.bbo.delta_speed_data_bbo import DeltaSpeedDataBBO
from blackboard.framework.abstract_knowledge_source import AbstractKnowledgeSource
from blackboard.framework.black_board import BlackBoard
from blackboard.framework.black_board_object import BlackBoardObject


class DeltaSpeedDataKS(AbstractKnowledgeSource):
    """DeltaSpeedDataBBO 를 BrakePedalBBO 로 바꾸어 Blackboard 에 추가한다.

    is_ready 를 참으로 설정해서 결정 단계에 도달했음을 알린다.
    지금은 process 가 메시지만 출력한다.
    """

    def is_interested(self, bbo: BlackBoardObject, bb: BlackBoard) -> bool:
        if isinstance(bbo, DeltaSpeedDataBBO):
            self._bbo = bbo
            self._bb = bb

            return True
        return False

    def process(self, bbo: BlackBoardObject) -> BlackBoardObject:
        brake_pedal_bbo = BrakePedalBBO()

        brake_pedal_bbo.set_ready(True)

        print("==>> DeltaSpeedDataKS processed DeltaSpeedDataBBO")
        return brake_pedal_bbo
