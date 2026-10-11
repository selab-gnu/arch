"""Java의 Test.main 에 해당하는 실행 진입점.

실행:  python -m mvc.main   (python/d2mvc 폴더에서)
"""
from .model import Model
from .view import View


def main() -> None:
    model = Model()
    view = View(model)
    model.set_votes(3)
    model.set_party("black")


if __name__ == "__main__":
    main()
