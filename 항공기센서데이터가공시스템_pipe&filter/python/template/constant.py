class Constant:
    """이 예제에서 사용하는 상수."""

    DEFAULT_PORT = 0          # 입력/출력 포트 index

    I_TIME = 0                # Flight data - time id
    I_ALTITUDE = 2            # Flight data - altitude id
    I_TEMPERATURE = 4         # Flight data - temperature id

    MEASUREMENT_LENGTH = 8    # 측정값 길이 (byte)
    ID_LENGTH = 4             # id 길이 (byte)

    # 콘솔에 출력되는 메시지
    TEMPERATURE_FILTER_MESSAGE = "::Temperature Reading"
    ALTITUDE_FILTER_MESSAGE = "::Altitude Reading"
    SINK_FILTER_MESSAGE = "::Sink Reading"
    SOURCE_FILTER_MESSAGE = "::Source reading file..."
    COMPLETE_MESSAGE = "::Flight report is created"

    # 입력/출력 파일 선택 메시지
    DIALOG_OUTPUT = "Select output file."
    DIALOG_INPUT = "Select Flight Data file"

    # 출력 파일 형식
    OUTPUT_HEADER = "Time\t\t\t\tAltitude\tTemperature\n============================================\n"
    OUTPUT_DATE_FORMAT = "%Y-%m-%d:%I:%M:%S"   # Java "yyyy-MM-dd:hh:mm:ss" (hh = 12시간제)
    OUTPUT_TEMPERATURE_DECIMAL_FORMAT = (3, 5)  # Java "000.00000" (정수 최소 3자리, 소수 5자리)
    OUTPUT_ALTITUDE_DECIMAL_FORMAT = (2, 5)     # Java "00.00000"  (정수 최소 2자리, 소수 5자리)
