from pipe_foundations.generator import Generator
from pipe_foundations.pipe import Pipe


class ExampleGenerator(Generator[int]):
    def generate_into(self, pipe: Pipe[int]) -> None:
        for i in range(1, 11):
            pipe.put(i)
            print(f"generated {i}")
            self.delay_for_debug(200)
        pipe.close_for_writing()
        print("generator finished")
