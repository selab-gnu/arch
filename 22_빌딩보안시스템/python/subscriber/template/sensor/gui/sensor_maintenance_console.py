from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Tuple

from common.template.constants import Constants
from common.template.gui_loop import run_later

if TYPE_CHECKING:
    from subscriber.template.sensor.gui.sensor_alarm import SensorAlarm


class SensorMaintenanceConsole(tk.Toplevel):
    """센서를 등록, 등록 해제하고 경보를 시험하는 관리 콘솔 창."""

    def __init__(self, associated_alarm: SensorAlarm, name: str, component_id: int,
                 alarm_bounds: Tuple[int, int, int, int]) -> None:
        super().__init__(associated_alarm)
        self._name = name
        self._associated_alarm = associated_alarm

        alarm_x, alarm_y, alarm_width, _ = alarm_bounds
        self.geometry(f"{Constants.SENSOR_TEST_CONSOLE_WIDTH}x{Constants.SENSOR_TEST_CONSOLE_HEIGHT}"
                      f"+{alarm_x + alarm_width}+{alarm_y}")
        self.title(f"{name}({component_id})")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        button_panel = tk.Frame(self)
        button_panel.pack(side=tk.BOTTOM, fill=tk.X)
        self._registration_btn = tk.Button(button_panel, text=Constants.REGISTER_BUTTON_TEXT,
                                           command=lambda: self._send(Constants.SENSOR_EVENT_REG))
        self._unregistration_btn = tk.Button(button_panel, text=Constants.UNREGISTER_BUTTON_TEXT,
                                             command=lambda: self._send(Constants.SENSOR_EVENT_UNREG))
        self._alarm_test_btn = tk.Button(button_panel, text="Alarm Test",
                                         command=self._associated_alarm.turn_on_alarm)
        for button in (self._registration_btn, self._unregistration_btn, self._alarm_test_btn):
            button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._message_area = tk.Text(self, bg="black", fg="white", yscrollcommand=scrollbar.set)
        self._message_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._message_area.yview)

        self.withdraw()  # Console 버튼을 누르면 나타난다

    def _send(self, event_req: int) -> None:
        self._associated_alarm.send_event(event_req)

    def turn_off_alarm(self) -> None:
        self._associated_alarm.turn_off_alarm()

    def print_message(self, message: str) -> None:
        run_later(self._append_message, message)

    def _append_message(self, message: str) -> None:
        self._message_area.insert(tk.END, message + "\n")
        self._message_area.see(tk.END)

    def set_id(self, component_id: int) -> None:
        self.title(f"{self._name}({component_id})")
