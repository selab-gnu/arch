"""Java 의 JFileChooser 대신 사용하는 파일 선택 도우미.

tkinter 가 있으면 파일 선택 창을 띄우고, 없으면(또는 창을 띄울 수 없으면) 콘솔에서 경로를 입력받는다.
선택을 취소하면 None 을 돌려준다.
"""
from typing import Optional

_FILETYPES = [("Flight Data File", "*.txt"), ("All files", "*")]


def _ask_console(title: str) -> Optional[str]:
    try:
        path = input(f"{title} (경로 입력, 빈 값이면 취소): ").strip()
    except EOFError:
        return None
    return path or None


def ask_open_file(title: str) -> Optional[str]:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(title=title, initialdir=".", filetypes=_FILETYPES)
        root.destroy()
        return path or None
    except Exception:  # tkinter 미설치, 디스플레이 없음 등
        return _ask_console(title)


def ask_save_file(title: str) -> Optional[str]:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(title=title, initialdir=".", filetypes=_FILETYPES)
        root.destroy()
        return path or None
    except Exception:
        return _ask_console(title)
