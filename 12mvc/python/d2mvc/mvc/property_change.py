"""Java 의 java.beans.PropertyChangeSupport / PropertyChangeListener 를 Python 으로 옮긴 것.

옵저버(Observer) 패턴: 모델은 리스너 목록만 알고, 값이 바뀌면 리스너들에게 알린다.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List


@dataclass
class PropertyChangeEvent:
    source: Any
    property_name: str
    old_value: Any
    new_value: Any


class PropertyChangeListener(ABC):
    @abstractmethod
    def property_change(self, evt: PropertyChangeEvent) -> None:
        ...


class PropertyChangeSupport:
    def __init__(self, source: Any) -> None:
        self._source = source
        self._listeners: List[PropertyChangeListener] = []

    def add_property_change_listener(self, listener: PropertyChangeListener) -> None:
        self._listeners.append(listener)

    def remove_property_change_listener(self, listener: PropertyChangeListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def fire_property_change(self, property_name: str, old_value: Any, new_value: Any) -> None:
        # Java 와 동일하게, 값이 실제로 바뀌었을 때만 알린다
        if old_value is not None and old_value == new_value:
            return
        evt = PropertyChangeEvent(self._source, property_name, old_value, new_value)
        for listener in list(self._listeners):
            listener.property_change(evt)
