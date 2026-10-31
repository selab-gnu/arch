from enum import Enum


class CommandEventID(Enum):
    """CommandEvent 의 메시지 값. 목표 Sensor 의 경보를 켜거나(TURNON) 끈다(TURNOFF)."""

    TURNOFF = 0
    TURNON = 1
