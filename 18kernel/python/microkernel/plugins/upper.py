from plugin import Plugin


class UpperPlugin(Plugin):
    name = "upper"

    def execute(self, text: str) -> str:
        return text.upper()
