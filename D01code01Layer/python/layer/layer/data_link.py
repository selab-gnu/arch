from .l1_provider import L1Provider


class DataLink(L1Provider):
    def l1_service(self) -> None:
        print("L1Service doing its job")
