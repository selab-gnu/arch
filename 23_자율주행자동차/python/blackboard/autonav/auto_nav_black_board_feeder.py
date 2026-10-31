"""Java의 AutoNavBlackBoardFeeder.main 에 해당하는 실행 진입점.

실행:  python3 -m blackboard.autonav.auto_nav_black_board_feeder   (python 폴더에서)
"""
import time
from typing import List

from blackboard.autonav.bb.auto_nav_black_board import AutoNavBlackBoard
from blackboard.autonav.bbo.front_vehicle_data_bbo import FrontVehicleDataBBO
from blackboard.autonav.bbo.right_lane_vehicle_data_bbo import RightLaneVehicleDataBBO
from blackboard.autonav.controller.auto_nav_bb_controller import AutoNavBBController
from blackboard.autonav.ks.delta_speed_data_ks import DeltaSpeedDataKS
from blackboard.autonav.ks.front_vehicle_data_ks import FrontVehicleDataKS
from blackboard.autonav.ks.right_lane_vehicle_data_ks import RightLaneVehicleDataKS
from blackboard.framework.knowledge_source import KnowledgeSource


class AutoNavBlackBoardFeeder:
    """Blackboard 시스템을 초기화하고 구동한다.

    1. Controller 에 Knowledge Source 를 추가한다
    2. Blackboard 에 Controller 를 등록한다
    3. Blackboard 에 BlackBoardObject 를 추가한다
    """

    def __init__(self) -> None:
        self.bb = AutoNavBlackBoard()
        self.controller = AutoNavBBController()

    def add_black_board_objects(self) -> None:
        """센서 데이터를 Blackboard 에 추가한다."""
        i = 0
        while i < 2:
            self.bb.add_black_board_object(FrontVehicleDataBBO())
            self.bb.add_black_board_object(RightLaneVehicleDataBBO())
            time.sleep(1)
            i += 1

    def add_controller(self) -> None:
        self.bb.add_observer(self.controller)

    def add_knowledge_sources(self) -> None:
        ks_list: List[KnowledgeSource] = []
        ks_list.append(RightLaneVehicleDataKS())
        ks_list.append(FrontVehicleDataKS())
        ks_list.append(DeltaSpeedDataKS())
        self.controller.set_knowledge_source_list(ks_list)


def main() -> None:
    feeder = AutoNavBlackBoardFeeder()

    feeder.add_knowledge_sources()
    feeder.add_controller()
    feeder.add_black_board_objects()


if __name__ == "__main__":
    main()
