import time

from blackboard.autonav.bbo.delta_speed_data_bbo import DeltaSpeedDataBBO
from blackboard.autonav.bbo.right_lane_vehicle_data_bbo import RightLaneVehicleDataBBO
from blackboard.framework.abstract_knowledge_source import AbstractKnowledgeSource
from blackboard.framework.black_board import BlackBoard
from blackboard.framework.black_board_object import BlackBoardObject


class RightLaneVehicleDataKS(AbstractKnowledgeSource):
    """RightLaneVehicleDataBBO 를 DeltaSpeedDataBBO 로 바꾸어 Blackboard 에 추가한다.

    지금은 process 가 메시지만 출력한다.
    """

    def is_interested(self, bbo: BlackBoardObject, bb: BlackBoard) -> bool:
        if isinstance(bbo, RightLaneVehicleDataBBO):
            self._bbo = bbo
            self._bb = bb

            return True

        return False

    def process(self, bbo: BlackBoardObject) -> BlackBoardObject:
        delta_speed_bbo = DeltaSpeedDataBBO()
        # TODO: RightLaneVehicleData 로 DeltaSpeed 를 계산한다

        time.sleep(1.2)

        print("==>> RightLaneVehicleDataKS processed RightLaneVehicleDataBBO")

        return delta_speed_bbo
