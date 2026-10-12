import struct

from framework.pf_general_filter import PFGeneralFilter

from .constant import Constant


class TemperatureFilterTemplate(PFGeneralFilter):
    """바이트를 flight data 로 복구해 화씨온도를 섭씨온도로 바꾼 뒤, 다시 바이트로 바꿔 다음 필터로 보낸다."""

    @staticmethod
    def fahrenheit_to_celsius(fahrenheit: float) -> float:
        return (5.0 / 9.0) * (fahrenheit - 32.0)

    def compute(self) -> None:
        print(Constant.TEMPERATURE_FILTER_MESSAGE)

        # 데이터 복구: id(4바이트 정수) + measurement(8바이트), 모두 big-endian
        id_bytes = self.read_bytes(Constant.ID_LENGTH, Constant.DEFAULT_PORT)
        measurement = self.read_bytes(Constant.MEASUREMENT_LENGTH, Constant.DEFAULT_PORT)
        data_id = int.from_bytes(id_bytes, "big")

        # 온도 변환 (measurement 는 8바이트 double)
        if data_id == Constant.I_TEMPERATURE:
            fahrenheit = struct.unpack(">d", measurement)[0]
            measurement = struct.pack(">d", self.fahrenheit_to_celsius(fahrenheit))

        # 다시 바이트로 만들어 전송
        self.out_ports[Constant.DEFAULT_PORT].write(id_bytes + measurement)
