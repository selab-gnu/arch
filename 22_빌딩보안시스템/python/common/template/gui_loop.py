"""tkinter 메인 루프 도우미.

tkinter 는 메인 스레드에서만 다뤄야 한다. 다른 스레드(이벤트 큐 회수, RMI 요청 처리)는
화면을 직접 고치지 않고 run_later() 로 작업을 넘기고, 메인 스레드가 주기적으로 꺼내 실행한다.
"""
import queue
import signal
import sys
from typing import Any, Callable, Optional

try:
    import tkinter as tk
except ImportError:
    sys.exit("tkinter 를 찾을 수 없습니다. README.md 의 '실행 환경' 을 참고하세요.")

_PUMP_INTERVAL_MS = 50

_root: Optional[tk.Tk] = None
_tasks: "queue.Queue[tuple]" = queue.Queue()


def get_root() -> tk.Tk:
    """모든 창의 부모가 되는 숨겨진 루트 창을 돌려준다."""
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()
    return _root


def run_later(task: Callable[..., Any], *args: Any) -> None:
    _tasks.put((task, args))


def _pump() -> None:
    try:
        while True:
            task, args = _tasks.get_nowait()
            task(*args)
    except queue.Empty:
        pass
    finally:
        get_root().after(_PUMP_INTERVAL_MS, _pump)


def _exit_on_signal(signum: int, frame: Any) -> None:
    sys.exit(0)  # atexit 에 등록한 등록 해제가 실행되도록 정상 종료한다


def mainloop() -> None:
    signal.signal(signal.SIGTERM, _exit_on_signal)
    signal.signal(signal.SIGINT, _exit_on_signal)
    _pump()
    get_root().mainloop()
