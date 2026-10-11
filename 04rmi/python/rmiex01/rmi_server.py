"""원격 객체를 만들어 레지스트리에 등록하는 서버.

실행:  python rmi_server.py   (python/rmiex01 폴더에서, 먼저 실행)
"""
import naming
from rmi_server_intf import RmiServerIntf


class RmiServer(RmiServerIntf):
    MESSAGE = "Hello World"

    def get_message(self) -> str:
        return self.MESSAGE


def main() -> None:
    print("RMI server started")

    try:
        registry = naming.create_registry(naming.DEFAULT_PORT)
        print("python RMI registry created.")
    except OSError:
        print("python RMI registry already exists (port in use).")
        return

    # 서버 객체를 만들고 "RmiServer" 라는 이름으로 등록
    server = RmiServer()
    registry.rebind("RmiServer", server)
    print("PeerServer bound in registry")

    try:
        registry.serve_forever()  # Ctrl+C 로 종료
    except KeyboardInterrupt:
        print("\nRMI server stopped")


if __name__ == "__main__":
    main()
