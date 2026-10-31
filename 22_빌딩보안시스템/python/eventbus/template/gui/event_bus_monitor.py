import tkinter as tk

from common.template.component_type import ComponentType
from common.template.constants import Constants
from common.template.gui_loop import get_root, run_later


class EventBusMonitor(tk.Toplevel):
    """Event Bus Server 를 모니터링하는 GUI 창."""

    def __init__(self) -> None:
        super().__init__(get_root())
        self.title(ComponentType.EVENTBUS_MONITOR.get_string_value())
        self.protocol("WM_DELETE_WINDOW", get_root().destroy)
        x, y, width, height = Constants.get_bounds(ComponentType.EVENTBUS_MONITOR)
        self.geometry(f"{width}x{height}+{x}+{y}")

        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._message_area = tk.Text(self, bg="black", fg="white", yscrollcommand=scrollbar.set)
        self._message_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._message_area.yview)

    def print_message(self, message: str) -> None:
        run_later(self._append_message, message)

    def _append_message(self, message: str) -> None:
        self._message_area.insert(tk.END, message + "\n")
        self._message_area.see(tk.END)
