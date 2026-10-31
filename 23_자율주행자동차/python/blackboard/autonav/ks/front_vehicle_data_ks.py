import time

from blackboard.autonav.bbo.delta_speed_data_bbo import DeltaSpeedDataBBO
from blackboard.autonav.bbo.front_vehicle_data_bbo import FrontVehicleDataBBO
from blackboard.framework.abstract_knowledge_source import AbstractKnowledgeSource
from blackboard.framework.black_board import BlackBoard
from blackboard.framework.black_board_object import BlackBoardObject


class FrontVehicleDataKS(AbstractKnowledgeSource):
    """FrontVehicleDataBBO 를 DeltaSpeedDataBBO 로 바꾸어 Blackboard 에 추가한다.

    지금은 process 가 메시지만 출력한다.
    """

    def is_interested(self, bbo: BlackBoardObject, bb: BlackBoard) -> bool:
        if isinstance(bbo, FrontVehicleDataBBO):
            self._bbo = bbo
            self._bb = bb

            return True

        return False

    def process(self, bbo: BlackBoardObject) -> BlackBoardObject:
        delta_speed_data_bbo = DeltaSpeedDataBBO()

        # Knowledge Source 가 작업하는 시간을 흉내 낸다
        time.sleep(1.0)

        print("==>> FrontVehicleDataKS processed FrontVehicleDataBBO")
        return delta_speed_data_bbo
