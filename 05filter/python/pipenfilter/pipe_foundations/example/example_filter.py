from pipe_foundations.simple_filter import SimpleFilter


class ExampleFilter(SimpleFilter[int, str]):
    """정수를 문자열로 바꾸는 필터."""

    def transform_one(self, item: int) -> str:
        out = str(item)
        print(f"filtered {item} to {out}")
        self.delay_for_debug(100)
        return out
