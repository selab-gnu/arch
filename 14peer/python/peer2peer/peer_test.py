"""Java의 PeerTest.main 에 해당하는 실행 진입점.

한 프로세스(피어)가 서버 스레드와 클라이언트 스레드를 함께 실행한다.

실행 (터미널 두 개에서):
    python peer_test.py 5020 5021     # 피어 A: 5020 에서 받고, 5021 로 보낸다
    python peer_test.py 5021 5020     # 피어 B: 5021 에서 받고, 5020 으로 보낸다
"""
import sys
import threading
import time

from simple_client import SimpleClient
from simple_server import SimpleServer


def main() -> None:
    server_port = int(sys.argv[1]) if len(sys.argv) > 1 else 5020
    client_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5021
    print(f"listening on {server_port}, sending to {client_port} (type 'exit' to quit)")

    server_thread = threading.Thread(target=SimpleServer(server_port).run)
    client_thread = threading.Thread(target=SimpleClient(client_port).run)
    server_thread.start()
    time.sleep(3)
    client_thread.start()


if __name__ == "__main__":
    main()
