"""코어를 시작하고 플러그인을 실행해 보는 진입점.

실행:  python main.py   (python/microkernel 폴더에서)
"""
from kernel import Kernel


def main() -> None:
    kernel = Kernel()
    kernel.load_plugins()
    print(f"plugins: {kernel.plugin_names()}")

    text = "hello micro kernel"
    print(f"input: {text}")
    for name in kernel.plugin_names():
        print(f"{name}: {kernel.execute(name, text)}")
    print(f"translate: {kernel.execute('translate', text)}")


if __name__ == "__main__":
    main()
