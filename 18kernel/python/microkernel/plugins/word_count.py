from plugin import Plugin


class WordCountPlugin(Plugin):
    name = "word_count"

    def execute(self, text: str) -> str:
        return str(len(text.split()))
