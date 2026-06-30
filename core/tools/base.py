import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger("pings.tools.base")


class BaseTool(ABC):
    name: str = "base"
    description: str = "Base tool"
    trigger_patterns: List[str] = []
    priority: int = 0

    @abstractmethod
    async def run(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self._enabled: bool = True

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def unregister(self, name: str) -> None:
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")

    def match(self, message: str) -> Optional[BaseTool]:
        if not self._enabled:
            return None
        message_lower = message.lower()
        best_match: Optional[BaseTool] = None
        best_priority = -1
        for tool in self._tools.values():
            for pattern in tool.trigger_patterns:
                if pattern.lower() in message_lower:
                    if tool.priority > best_priority:
                        best_priority = tool.priority
                        best_match = tool
                    break
        return best_match

    def get_all(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def reset(self) -> None:
        self._tools.clear()
        logger.info("Tool registry reset")

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled


tool_registry = ToolRegistry()
