from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Dict

from common.template.component_type import ComponentType
from common.template.constants import Constants
from common.template.gui_loop import get_root, run_later
from event.template.command_event import CommandEvent
from event.template.command_event_id import CommandEventID

if TYPE_CHECKING:
    from subscriber.eb_abstract_subscriber import EBAbstractSubscriber


class ControlConsole(tk.Toplevel):
    """등록된 센서와 메시지를 확인하고, 특정 센서의 경보를 해제하는 사용자 인터페이스."""

    def __init__(self, subscriber: EBAbstractSubscriber) -> None:
        super().__init__(get_root(), bg="white")
        self._subscriber = subscriber
        self._sensors_buttons: Dict[int, SensorButton] = {}

        x, y, width, height = Constants.get_bounds(ComponentType.CONTROL_CONSOLE)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.title(ComponentType.CONTROL_CONSOLE.get_string_value())
        self.protocol("WM_DELETE_WINDOW", get_root().destroy)

        self._logo = tk.PhotoImage(file=Constants.LOGO_IMAGE)
        logo_width, logo_height = self._logo.width(), self._logo.height()
        tk.Label(self, image=self._logo, bg="white", bd=0).place(x=10, y=10)

        self._register_btn = tk.Button(self, text=Constants.REGISTER_BUTTON_TEXT, command=subscriber.register)
        self._register_btn.place(x=10 + logo_width, y=10 + logo_height, anchor="sw")
        self._unregister_btn = tk.Button(self, text=Constants.UNREGISTER_BUTTON_TEXT, command=subscriber.unregister)
        self._unregister_btn.place(x=10 + logo_width + self._register_btn.winfo_reqwidth(),
                                   y=10 + logo_height, anchor="sw")

        main_pane = tk.Frame(self, bg="white")
        main_pane.place(x=10, y=10 + logo_height, width=416, height=362 - logo_height)
        tk.Label(main_pane, text=Constants.CONSOLE_LABEL, bg="white", fg="black", anchor="w").pack(fill=tk.X)
        scrollbar = tk.Scrollbar(main_pane)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._message_area = tk.Text(main_pane, bg="black", fg="white", yscrollcommand=scrollbar.set)
        self._message_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._message_area.yview)

        self._sensors_panel = tk.Frame(self, bg="white", highlightbackground="black", highlightthickness=1)
        self._sensors_panel.place(x=432, y=10 + logo_height, width=158, height=362 - logo_height)
        tk.Label(self._sensors_panel, text=Constants.SENSORS_LIST_LABEL, bg="white", fg="black",
                 relief=tk.RAISED).pack(fill=tk.X)

    def add_new_sensor(self, sensor_name: str, sensor_id: int) -> None:
        run_later(self._add_sensor_button, sensor_name, sensor_id)

    def _add_sensor_button(self, sensor_name: str, sensor_id: int) -> None:
        sensor_btn = SensorButton(self._sensors_panel, sensor_name, sensor_id, self._turn_off_alarm)
        self._sensors_buttons[sensor_id] = sensor_btn
        sensor_btn.pack(fill=tk.X)

    def print_message(self, message: str) -> None:
        run_later(self._append_message, message)

    def _append_message(self, message: str) -> None:
        self._message_area.insert(tk.END, message + "\n")
        self._message_area.see(tk.END)

    def turn_on_indicator(self, sensor_id: int) -> None:
        run_later(self._set_indicator, sensor_id, True)

    def turn_off_indicator(self, sensor_id: int) -> None:
        run_later(self._set_indicator, sensor_id, False)

    def _set_indicator(self, sensor_id: int, is_turned: bool) -> None:
        self._sensors_buttons[sensor_id].turn_on(is_turned)

    def unregister_sensor(self, sensor_id: int) -> None:
        run_later(self._remove_sensor_button, sensor_id)

    def _remove_sensor_button(self, sensor_id: int) -> None:
        self._sensors_buttons.pop(sensor_id).destroy()

    def _turn_off_alarm(self, component_id: int) -> None:
        self._subscriber.send_event(CommandEvent(CommandEventID.TURNOFF, component_id))
        self.turn_off_indicator(component_id)


class SensorButton(tk.Frame):
    """Control Console 에 등록된 각각의 센서를 표현하는 GUI 컴포넌트."""

    def __init__(self, parent: tk.Widget, sensor_name: str, sensor_id: int, on_turn_off) -> None:
        super().__init__(parent, bg="white", height=80)
        self._name_label = tk.Label(self, text=f"Name: {sensor_name}", bg="white", fg="black", anchor="w")
        self._id_label = tk.Label(self, text=f"ID: {sensor_id}", bg="white", fg="black", anchor="w")
        self._turn_off_btn = tk.Button(self, text="Turn Off", command=lambda: on_turn_off(sensor_id))
        for widget in (self._name_label, self._id_label, self._turn_off_btn):
            widget.pack(fill=tk.X)
        self.turn_on(False)

    def turn_on(self, is_turned: bool) -> None:
        if is_turned:
            self._turn_off_btn.config(state=tk.NORMAL, fg="red")
        else:
            self._turn_off_btn.config(state=tk.DISABLED, fg="blue")
