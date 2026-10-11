import os
import socket


class SimpleServer:
    """다른 피어가 보낸 메시지를 받아 출력하는 서버 역할."""

    def __init__(self, port: int = 5020) -> None:
        self.port = port

    def play(self) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                listener.bind(("", self.port))
                listener.listen(1)
                conn, _addr = listener.accept()
                print("Connected!")
                with conn, conn.makefile("r", encoding="utf-8") as reader:
                    for line in reader:  # 한 줄씩 읽음. 상대가 연결을 끊으면 반복이 끝남
                        input_message = line.rstrip("\n")
                        if input_message.lower() == "exit":
                            break
                        print(f"Peer: {input_message}")
        except OSError as e:
            print(f"[server] {e}")
        finally:
            # Java 의 System.exit(0) 처럼 프로세스 전체(클라이언트 스레드 포함)를 종료
            os._exit(0)

    def run(self) -> None:
        self.play()
