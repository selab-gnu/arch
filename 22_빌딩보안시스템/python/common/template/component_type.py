from enum import Enum


class ComponentType(Enum):
    """빌딩 보안시스템에 존재하는 컴포넌트들의 타입."""

    EVENTBUS_MONITOR = "Event Bus Monitor"
    CONTROL_CONSOLE = "Control Console"
    DOOR = "Door"
    DRONE = "Drone"
    WINDOW = "Window"

    def get_string_value(self) -> str:
        return self.value
