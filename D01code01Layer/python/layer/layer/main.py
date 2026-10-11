"""Java의 Test.main 에 해당하는 실행 진입점.

실행:  python -m layer.main   (python/layer 폴더에서)
"""
from .data_link import DataLink
from .session import Session
from .transport import Transport


def main() -> None:
    data_link = DataLink()
    transport = Transport()
    session = Session()

    transport.set_lower_layer(data_link)
    session.set_lower_layer(transport)

    session.l3_service()


if __name__ == "__main__":
    main()
