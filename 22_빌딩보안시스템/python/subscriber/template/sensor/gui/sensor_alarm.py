from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from common.template.component_type import ComponentType
from common.template.constants import Constants
from common.template.gui_loop import get_root, run_later
from event.template.notification_event import NotificationEvent
from event.template.notification_event_id import NotificationEventID
from event.template.registration_event import RegistrationEvent
from subscriber.template.sensor.gui.sensor_maintenance_console import SensorMaintenanceConsole

if TYPE_CHECKING:
    from subscriber.eb_abstract_subscriber import EBAbstractSubscriber

_BLINK_INTERVAL_MS = 200


class SensorAlarm(tk.Toplevel):
    """센서의 경보를 띄우는 GUI 창."""

    def __init__(self, name: str, component_id: int, component_type: ComponentType,
                 subscriber: EBAbstractSubscriber) -> None:
        super().__init__(get_root())
        self._subscriber = subscriber
        self._type = component_type
        self._is_tresspassing = False
        self._is_blinking = False

        self.title(name)
        self.protocol("WM_DELETE_WINDOW", get_root().destroy)
        x, y, width, height = Constants.get_bounds(component_type)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.columnconfigure(0, weight=1)
        for row in range(3):
            self.rowconfigure(row, weight=1, uniform="alarm")

        info_panel = tk.Frame(self, bg="white")
        info_panel.grid(row=0, column=0, sticky="nsew")
        self._name_label = tk.Label(info_panel, text=f"Name: {name}", bg="white", fg="black", anchor="w")
        self._id_label = tk.Label(info_panel, text=f"ID: {component_id}", bg="white", fg="black", anchor="w")
        self._status_label = tk.Label(info_panel, text=Constants.SENSOR_STATUS_IDLE, bg="white", fg="black", anchor="w")
        for label in (self._name_label, self._id_label, self._status_label):
            label.pack(fill=tk.X)

        self._alarm_panel = tk.Frame(self, bg="white")
        self._alarm_panel.grid(row=1, column=0, sticky="nsew")

        self._test_console_btn = tk.Button(self, text="Console", command=self._show_maintenance_console)
        self._test_console_btn.grid(row=2, column=0, sticky="nsew")

        self._maintenance_console = SensorMaintenanceConsole(self, name, component_id, (x, y, width, height))

    def turn_on_alarm(self) -> None:
        self.send_event(Constants.SENSOR_EVENT_TRESSPASISNG)
        run_later(self._start_alarm)

    def _start_alarm(self) -> None:
        self._change_status(True)
        if not self._is_blinking:
            self._is_blinking = True
            self._blink()

    def _blink(self) -> None:
        # Java 는 경보 스레드에서 sleep 하지만, tkinter 는 after 로 주기 작업을 예약한다
        if self._is_tresspassing:
            next_color = "blue" if self._alarm_panel.cget("bg") == "red" else "red"
            self._alarm_panel.config(bg=next_color)
            self.after(_BLINK_INTERVAL_MS, self._blink)
        else:
            self._is_blinking = False

    def set_id(self, component_id: int) -> None:
        run_later(self._update_id, component_id)

    def _update_id(self, component_id: int) -> None:
        self._id_label.config(text=f"ID: {component_id}")
        self._maintenance_console.set_id(component_id)

    def print_message(self, message: str) -> None:
        self._maintenance_console.print_message(message)

    def turn_off_alarm(self) -> None:
        run_later(self._stop_alarm)

    def _stop_alarm(self) -> None:
        self._change_status(False)
        self._alarm_panel.config(bg="white")

    def send_event(self, event_req_from_maintenance_console: int) -> None:
        subscriber = self._subscriber
        if event_req_from_maintenance_console == Constants.SENSOR_EVENT_REG:
            if subscriber.get_component_id() == -1:
                subscriber.register()
                self.set_id(subscriber.get_component_id())
                subscriber.send_event(RegistrationEvent(self._type, subscriber.get_component_id()))
            else:
                self.print_message("이미 등록된 컴포넌트입니다.")
        elif event_req_from_maintenance_console == Constants.SENSOR_EVENT_UNREG:
            if subscriber.get_component_id() != -1:
                subscriber.unregister()
                self.set_id(subscriber.get_component_id())
                subscriber.send_event(
                    NotificationEvent(NotificationEventID.UNREGISTRATION, subscriber.get_component_id()))
            else:
                self.print_message("이미 등록해제된 컴포넌트입니다.")
        elif event_req_from_maintenance_console == Constants.SENSOR_EVENT_TRESSPASISNG:
            if subscriber.get_component_id() != -1:
                subscriber.send_event(
                    NotificationEvent(NotificationEventID.TRESPASSING, subscriber.get_component_id()))
            else:
                self.print_message("침입 발생!! 침입 발생!!")

    def _change_status(self, new_status: bool) -> None:
        if new_status:
            self._status_label.config(text=Constants.SENSOR_STATUS_TRESSPASSING)
        else:
            self._status_label.config(text=Constants.SENSOR_STATUS_IDLE)
        self._is_tresspassing = new_status

    def _show_maintenance_console(self) -> None:
        self._maintenance_console.deiconify()
