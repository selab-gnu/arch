from event.eb_default_event import EBDefaultEvent
from event.template.command_event_id import CommandEventID


class CommandEvent(EBDefaultEvent):
    """Control Console 에서 특정 센서의 경보를 끌 때 사용한다. 목표 Subscriber 의 ID 를 함께 전송한다."""

    message_type = CommandEventID

    def __init__(self, command_event_id: CommandEventID, target_component_id: int) -> None:
        super().__init__(command_event_id, target_component_id)
