import struct
from datetime import datetime
from typing import Optional, Tuple

from framework.pf_general_filter import EndOfStreamException, PFGeneralFilter

from .constant import Constant
from .file_dialog import ask_save_file


def format_decimal(value: float, pattern: Tuple[int, int]) -> str:
    """Java DecimalFormat("000.00000") 처럼 정수부를 최소 자릿수까지 0으로 채운다."""
    int_digits, frac_digits = pattern
    text = f"{abs(value):.{frac_digits}f}"
    int_part, frac_part = text.split(".")
    sign = "-" if value < 0 else ""
    return f"{sign}{int_part.zfill(int_digits)}.{frac_part}"


class SinkFilterTemplate(PFGeneralFilter):
    """들어온 바이트를 읽어 시간/고도/온도 보고서를 파일로 출력하는 필터."""

    def __init__(self) -> None:
        super().__init__()
        self.out_file: Optional[str] = None

    def set_output_file(self, path: Optional[str] = None) -> None:
        """출력 파일 경로를 정한다. path 가 없으면 파일 선택 창을 띄운다."""
        self.out_file = path or ask_save_file(Constant.DIALOG_OUTPUT)

    def compute(self) -> None:
        if self.out_file is None:
            raise EndOfStreamException()

        print(Constant.SINK_FILTER_MESSAGE)
        output_data = []

        try:
            while True:
                # 데이터 복구
                data_id = int.from_bytes(self.read_bytes(Constant.ID_LENGTH), "big")
                measurement = self.read_bytes(Constant.MEASUREMENT_LENGTH)

                # 변환
                if data_id == Constant.I_TIME:          # 시간: 8바이트 long (epoch milliseconds)
                    millis = struct.unpack(">q", measurement)[0]
                    timestamp = datetime.fromtimestamp(millis / 1000)
                    output_data.append(timestamp.strftime(Constant.OUTPUT_DATE_FORMAT) + "\t")
                elif data_id == Constant.I_ALTITUDE:    # 고도: 8바이트 double
                    altitude = struct.unpack(">d", measurement)[0]
                    output_data.append(format_decimal(altitude, Constant.OUTPUT_ALTITUDE_DECIMAL_FORMAT) + "\t")
                elif data_id == Constant.I_TEMPERATURE: # 온도: 8바이트 double
                    temperature = struct.unpack(">d", measurement)[0]
                    output_data.append(format_decimal(temperature, Constant.OUTPUT_TEMPERATURE_DECIMAL_FORMAT) + "\n")
        except EndOfStreamException:
            print(Constant.COMPLETE_MESSAGE)

        with open(self.out_file, "w", encoding="utf-8", newline="") as fw:
            fw.write(Constant.OUTPUT_HEADER)
            fw.write("".join(output_data))

        raise EndOfStreamException()
