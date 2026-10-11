from client import Client
from service import Service


class PrintService(Service):
    def __init__(self, svc: str, srv: str) -> None:
        self.nameofservice = svc  # 서비스 이름
        self.nameofserver = srv   # 서버 이름
        self.greeting = ""
        # 생성되면서 스스로 Dispatcher 에 등록한다
        Client.dsp.register_service(self.nameofservice, self)

    def run_service(self) -> None:
        print(f"Service:  {self.nameofservice} by {self.nameofserver}")
