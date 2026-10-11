"""Java의 TestMaster.main 에 해당하는 실행 진입점.

실행:  python test_master.py   (python/d4MasterSlave1 폴더에서)
"""
from master import Master


def main() -> None:
    master = Master()
    master.run()


if __name__ == "__main__":
    main()
