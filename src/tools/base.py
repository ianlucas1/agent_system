from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolInput:
    operation_name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolOutput:
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Tool(ABC):
    @abstractmethod
    def execute(self, tool_input: ToolInput) -> ToolOutput:
        pass
