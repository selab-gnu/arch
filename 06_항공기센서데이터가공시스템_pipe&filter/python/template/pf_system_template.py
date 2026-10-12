import threading
from typing import Optional

from .altitude_filter_template import AltitudeFilterTemplate
from .constant import Constant
from .sink_filter_template import SinkFilterTemplate
from .source_filter_template import SourceFilterTemplate
from .temperature_filter_template import TemperatureFilterTemplate


class PFSystemTemplate:
    """사용자 정의 필터들을 만들고, 초기값을 정하고, 연결해서 실행한다. framework.pf_system_main 에서 사용한다."""

    def __init__(self) -> None:
        self.source_filter = SourceFilterTemplate()
        self.temperature_filter = TemperatureFilterTemplate()
        self.altitude_filter = AltitudeFilterTemplate()
        self.sink_filter = SinkFilterTemplate()

    def init(self, input_file: Optional[str] = None, output_file: Optional[str] = None) -> None:
        """필터 외의 초기 설정 (입력/출력 파일 지정)."""
        does_continue = self.source_filter.set_input_file(input_file)
        if does_continue:
            self.sink_filter.set_output_file(output_file)

    def filter_connection(self) -> None:
        """Source → Temperature → Altitude → Sink 순서로 필터를 연결한다."""
        self.source_filter.connect(Constant.DEFAULT_PORT,
                                   self.temperature_filter.get_input_port(Constant.DEFAULT_PORT))
        self.temperature_filter.connect(Constant.DEFAULT_PORT,
                                        self.altitude_filter.get_input_port(Constant.DEFAULT_PORT))
        self.altitude_filter.connect(Constant.DEFAULT_PORT,
                                     self.sink_filter.get_input_port(Constant.DEFAULT_PORT))

    def filter_execution(self) -> None:
        """각 필터를 별도의 스레드로 실행한다."""
        for f in (self.source_filter, self.temperature_filter, self.altitude_filter, self.sink_filter):
            threading.Thread(target=f.run, name=type(f).__name__).start()
