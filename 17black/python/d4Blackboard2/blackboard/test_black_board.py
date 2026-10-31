"""Java의 TestBlackBoard.main 에 해당하는 실행 진입점.

실행:  python -m blackboard.test_black_board   (python/d4Blackboard2 폴더에서)
"""
import traceback

from .black_board import BlackBoard
from .control_data import ControlData
from .worker1 import Worker1


def main() -> None:
    board = BlackBoard()

    worker1 = Worker1("PrimeFinder", board)
    board.add_knowledge_worker(worker1)

    int_array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    data = ControlData("PrimeNumbers", int_array)

    try:
        board.update("PrimeNumbers", data)
        board.control.loop()
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
