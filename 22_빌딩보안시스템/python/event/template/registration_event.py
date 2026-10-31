from common.template.component_type import ComponentType
from event.eb_default_event import EBDefaultEvent


class RegistrationEvent(EBDefaultEvent):
    """등록된 Sensor 의 종류와 ID 를 전송한다. Control Console 은 이 이벤트를 받아서 UI 를 생성한다."""

    message_type = ComponentType

    def __init__(self, component_type: ComponentType, component_id: int) -> None:
        super().__init__(component_type, component_id)
