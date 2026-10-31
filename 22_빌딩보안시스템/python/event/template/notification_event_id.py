from enum import Enum


class NotificationEventID(Enum):
    """NotificationEvent 의 메시지 값. Sensor 의 상태를 등록해제, 침입, 대기로 표현한다."""

    UNREGISTRATION = 0
    TRESPASSING = 1
    IDLE = 2
