from .l2_provider import L2Provider


class Transport(L2Provider):
    def l2_service(self) -> None:
        print("L2Service doing its job")
        self.level1.l1_service()
        print("L2Service ending its job")
