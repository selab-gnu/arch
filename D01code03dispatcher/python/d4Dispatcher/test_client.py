"""Java의 TestClient.main 에 해당하는 실행 진입점.

실행:  python test_client.py   (python/d4Dispatcher 폴더에서)
"""
from client import Client
from print_service import PrintService


def main() -> None:
    PrintService("printSvc", "srv1")
    PrintService("printSvc", "srv2")
    client = Client()
    client.do_task()


if __name__ == "__main__":
    main()
