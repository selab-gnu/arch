from pathlib import Path
from typing import Tuple

from common.template.component_type import ComponentType
from common.template.gui_loop import get_root


class Constants:
    """빌딩 보안시스템에서 사용되는 상수."""

    REGISTRATION = "This component is registered: "
    UNREGISTRATION = "This component is unregistered: "
    GETTINGANEVENTQUEUE = "Now getting Event Queue."
    TURNOFF_ALARM = " is turned off."
    TURNON_ALARM = " is turned on."
    EVENTSENT = "이The event is sent: "
    TRESPASSING = "TRESSPASSING!"
    IDLE = "IDLE."
    SENSOR_STATUS_IDLE = "IDLE"
    SENSOR_STATUS_TRESSPASSING = "TRESSPASSING!"

    LOGO_HEIGHT = 58
    # tkinter 는 JPEG 를 읽지 못하므로 java/resource/logo_nipa.jpg 를 GIF 로 변환해 사용한다
    LOGO_IMAGE = str(Path(__file__).resolve().parents[2] / "resource" / "logo_nipa.gif")

    REGISTER_BUTTON_TEXT = "Register"
    UNREGISTER_BUTTON_TEXT = "Unregister"

    CONSOLE_WINDOW_TITLE = "Control Console"
    CONSOLE_LABEL = "Message Window"
    SENSORS_LIST_LABEL = "Registered Sensors"

    SENSOR_EVENT_UNREG = 0
    SENSOR_EVENT_REG = 1
    SENSOR_EVENT_TRESSPASISNG = 2
    SENSOR_EVENT_IDLE = 3

    SENSOR_ALARM_WIDTH = 150
    SENSOR_ALARM_HEIGHT = 200
    SENSOR_TEST_CONSOLE_WIDTH = 300
    SENSOR_TEST_CONSOLE_HEIGHT = 200
    EVENTBUS_MONITOR_WIDTH = 300
    EVENTBUS_MONITOR_HEIGHT = 200
    CONTROL_CONSOLE_WIDTH = 600
    CONTROL_CONSOLE_HEIGHT = 400
    GAP = 50

    @staticmethod
    def get_sensor_add_message(component_id: str) -> str:
        return f"The sensor({component_id}) is added."

    @staticmethod
    def get_control_console_button_alert_text(name: str) -> str:
        return f"{name}\nWhite alert"

    @staticmethod
    def get_bounds(component_type: ComponentType) -> Tuple[int, int, int, int]:
        """각 컴포넌트 창의 위치와 크기 (x, y, width, height) 를 결정한다."""
        root = get_root()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        control_console_x = int(screen_width * 0.01)
        control_console_y = int(screen_height * 0.4)
        sensor_x = int(screen_width * 0.6)
        sensor_y = int(screen_height * 0.6)
        event_bus_x = int(screen_width * 0.01)
        event_bus_y = int(screen_height * 0.01)

        alarm_size = (Constants.SENSOR_ALARM_WIDTH, Constants.SENSOR_ALARM_HEIGHT)
        if component_type == ComponentType.DOOR:
            return (sensor_x, sensor_y, *alarm_size)
        if component_type == ComponentType.DRONE:
            return (sensor_x, sensor_y - Constants.SENSOR_ALARM_HEIGHT, *alarm_size)
        if component_type == ComponentType.WINDOW:
            return (sensor_x, sensor_y - Constants.SENSOR_ALARM_HEIGHT * 2, *alarm_size)
        if component_type == ComponentType.EVENTBUS_MONITOR:
            return (event_bus_x, event_bus_y, Constants.EVENTBUS_MONITOR_WIDTH, Constants.EVENTBUS_MONITOR_HEIGHT)
        return (control_console_x, control_console_y, Constants.CONTROL_CONSOLE_WIDTH, Constants.CONTROL_CONSOLE_HEIGHT)
