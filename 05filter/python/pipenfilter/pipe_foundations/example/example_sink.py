from pipe_foundations.pipe import Pipe
from pipe_foundations.sink import Sink


class ExampleSink(Sink[str]):
    def take_from(self, pipe: Pipe[str]) -> None:
        while (item := pipe.next_or_none_if_emptied()) is not None:
            print(item)
            self.delay_for_debug(300)
        print("sink finished")
