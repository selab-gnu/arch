from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .controller import Controller
from .property_change import PropertyChangeEvent, PropertyChangeListener

if TYPE_CHECKING:
    from .model import Model


class View(PropertyChangeListener):
    def __init__(self, model: Model) -> None:
        self.model = model
        self.controller: Optional[Controller] = None
        self.model.add_property_change_listener(self)
        self.make_controller()

    def make_controller(self) -> None:
        self.controller = Controller(self.model, self)
        self.model.add_property_change_listener(self.controller)

    def property_change(self, evt: PropertyChangeEvent) -> None:
        self.show()

    def show(self) -> None:
        print("View updates the information.")
        print(f"* party: {self.model.party}")
        print(f"* votes: {self.model.votes}")
