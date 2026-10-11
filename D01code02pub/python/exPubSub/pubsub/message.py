class Message:
    """게시자가 발행하는 메시지. topic(주제)과 payload(내용)를 가진다."""

    def __init__(self, topic: str = "", payload: str = "") -> None:
        self.topic = topic
        self.payload = payload
