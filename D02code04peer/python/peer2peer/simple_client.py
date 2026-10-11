import os
import socket
import time


class SimpleClient:
    """사용자가 입력한 메시지를 다른 피어에게 보내는 클라이언트 역할."""

    def __init__(self, port: int = 5021, host: str = "localhost", connect_timeout: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout

    def _connect(self) -> socket.socket:
        # 상대 피어의 서버가 아직 안 떠 있으면 잠시 기다렸다가 다시 시도한다
        deadline = time.time() + self.connect_timeout
        while True:
            try:
                return socket.create_connection((self.host, self.port))
            except ConnectionRefusedError:
                if time.time() > deadline:
                    raise
                print(f"[client] waiting for peer on port {self.port} ...")
                time.sleep(1)

    def play(self) -> None:
        try:
            with self._connect() as sock, sock.makefile("w", encoding="utf-8") as writer:
                while True:
                    try:
                        output_message = input()
                    except EOFError:  # 입력이 끝나면(Ctrl+D) exit 로 처리
                        output_message = "exit"
                    writer.write(output_message + "\n")
                    writer.flush()
                    if output_message.lower() == "exit":
                        break
        except OSError as e:
            print(f"[client] {e}")
        finally:
            os._exit(0)

    def run(self) -> None:
        self.play()
