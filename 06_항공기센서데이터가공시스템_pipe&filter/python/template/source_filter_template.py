from typing import Optional

from framework.pf_general_filter import EndOfStreamException, PFGeneralFilter

from .constant import Constant
from .file_dialog import ask_open_file


class SourceFilterTemplate(PFGeneralFilter):
    """입력 파일을 읽어 그 바이트들을 다음 필터로 넘기는 필터."""

    def __init__(self) -> None:
        super().__init__()
        self.input_file: Optional[str] = None

    def set_input_file(self, path: Optional[str] = None) -> bool:
        """입력 파일을 정한다. path 가 없으면 파일 선택 창을 띄운다. 선택되면 True."""
        self.input_file = path or ask_open_file(Constant.DIALOG_INPUT)
        return self.input_file is not None

    def compute(self) -> None:
        if self.input_file is None:
            raise EndOfStreamException()

        print(Constant.SOURCE_FILTER_MESSAGE)
        with open(self.input_file, "rb") as f:
            while True:
                databyte = f.read(1)  # 데이터 읽기
                if not databyte:      # 파일 끝
                    raise EndOfStreamException()
                self.out_ports[Constant.DEFAULT_PORT].write(databyte)  # 다음 필터로 전송
