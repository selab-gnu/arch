"""레지스트리에서 원격 객체를 찾아 메서드를 호출하는 클라이언트.

실행:  python rmi_client.py   (다른 터미널에서 rmi_server.py 를 먼저 실행해 둔 상태에서)
"""
import sys

import naming


def main() -> None:
    server = naming.lookup("//localhost/RmiServer")
    try:
        print(server.get_message())
    except ConnectionRefusedError:
        print("서버에 연결할 수 없습니다 (localhost:1099).\n"
              "다른 터미널에서 'python3 rmi_server.py' 를 먼저 실행하고, 그 터미널은 닫지 말고 그대로 두세요.",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
