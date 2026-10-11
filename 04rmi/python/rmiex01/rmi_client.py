"""레지스트리에서 원격 객체를 찾아 메서드를 호출하는 클라이언트.

실행:  python rmi_client.py   (rmi_server.py 를 먼저 실행해 둔 상태에서)
"""
import naming


def main() -> None:
    server = naming.lookup("//localhost/RmiServer")
    print(server.get_message())


if __name__ == "__main__":
    main()
