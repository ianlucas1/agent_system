"""tools.memory

Provides MemoryTool for interacting with the shared ContextBus memory store.
"""
from __future__ import annotations

from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry
from src.shared.context_bus import ContextBus


class MemoryTool(Tool):
    """Tool for shared memory operations via ContextBus."""

    def __init__(self, bus: ContextBus | None = None) -> None:
        self.bus = bus or ContextBus()

    def execute(self, tool_input: ToolInput) -> ToolOutput:
        op = tool_input.operation_name.lower().strip()
        args = tool_input.args or {}
        key = args.get("key")
        value = args.get("value")
        # Validate key
        if not key or not isinstance(key, str):
            return ToolOutput(success=False, error="MemoryTool: 'key' must be provided and a string.")
        # Dispatch operations
        if op == "get":
            result = self.bus.get(key)
            message = result if result is not None else ""
            return ToolOutput(success=True, message=message, data={"value": result})
        if op == "set":
            if value is None or not isinstance(value, str):
                return ToolOutput(success=False, error="MemoryTool: 'value' must be provided and a string for set.")
            self.bus.set(key, value)
            return ToolOutput(success=True, message=value, data={"value": value})
        if op == "append":
            if value is None or not isinstance(value, str):
                return ToolOutput(success=False, error="MemoryTool: 'value' must be provided and a string for append.")
            self.bus.append(key, value)
            new_val = self.bus.get(key)
            message = new_val if new_val is not None else ""
            return ToolOutput(success=True, message=message, data={"value": new_val})
        # Unsupported operation
        return ToolOutput(success=False, error=f"Unsupported MemoryTool operation: {op}")


# Register the tool globally
ToolRegistry.register("memory", MemoryTool()) 