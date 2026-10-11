from __future__ import annotations

from typing import TYPE_CHECKING

from .property_change import PropertyChangeEvent, PropertyChangeListener

if TYPE_CHECKING:
    from .model import Model
    from .view import View


class Controller(PropertyChangeListener):
    def __init__(self, model: Model, view: View) -> None:
        self.model = model
        self.view = view

    def property_change(self, evt: PropertyChangeEvent) -> None:
        print(f"the controller notices the change of the model:{evt.property_name}")
