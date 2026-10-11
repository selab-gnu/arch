from .l3_provider import L3Provider


class Session(L3Provider):
    def l3_service(self) -> None:
        print("L3Service starting its job")
        self.level2.l2_service()
        print("L3Service ending its job")
