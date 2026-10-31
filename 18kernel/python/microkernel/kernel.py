import importlib
import inspect
import pkgutil
from typing import Dict, List

import plugins
from plugin import Plugin


class Kernel:
    """코어 시스템. 플러그인을 찾아 등록하고 실행할 뿐, 개별 기능은 알지 못한다."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.name] = plugin

    def unregister(self, name: str) -> None:
        self._plugins.pop(name, None)

    def plugin_names(self) -> List[str]:
        return sorted(self._plugins)

    def load_plugins(self) -> None:
        """plugins 폴더의 모듈을 읽어 Plugin 을 상속한 클래스를 모두 등록한다."""
        for module_info in pkgutil.iter_modules(plugins.__path__):
            module = importlib.import_module(f"plugins.{module_info.name}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, Plugin) and cls is not Plugin:
                    self.register(cls())

    def execute(self, name: str, text: str) -> str:
        plugin = self._plugins.get(name)
        if plugin is None:
            return f"error: unknown plugin '{name}'"
        # 플러그인이 실패해도 코어는 멈추지 않는다
        try:
            return plugin.execute(text)
        except Exception as e:
            return f"error: plugin '{name}' failed: {e}"
