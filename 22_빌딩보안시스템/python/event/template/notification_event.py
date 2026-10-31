from event.eb_default_event import EBDefaultEvent
from event.template.notification_event_id import NotificationEventID


class NotificationEvent(EBDefaultEvent):
    """Sensor 의 침입, 대기, 등록해제를 알린다. 알림을 발생시킨 Subscriber 의 ID 를 함께 전송한다."""

    message_type = NotificationEventID

    def __init__(self, notification_event_id: NotificationEventID, component_id: int) -> None:
        super().__init__(notification_event_id, component_id)
