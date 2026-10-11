"""Java의 ExampleRunner.main 에 해당하는 실행 진입점.

실행:  python -m pipe_foundations.example.example_runner   (python/pipenfilter 폴더에서)
"""
from pipe_foundations.pipe_impl import PipeImpl

from .example_filter import ExampleFilter
from .example_generator import ExampleGenerator
from .example_sink import ExampleSink


def main() -> None:
    # 파이프 생성
    gen_to_filter: PipeImpl[int] = PipeImpl()
    filter_to_out: PipeImpl[str] = PipeImpl()

    # 파이프를 사용하는 컴포넌트 생성
    generator = ExampleGenerator(gen_to_filter)
    filter_ = ExampleFilter(gen_to_filter, filter_to_out)
    sink = ExampleSink(filter_to_out)

    # 모든 컴포넌트 시작 (각각 별도 스레드)
    generator.start()
    filter_.start()
    sink.start()

    # main 스레드는 먼저 끝나지만, 나머지 스레드는 계속 실행된다
    print("runner finished")


if __name__ == "__main__":
    main()
