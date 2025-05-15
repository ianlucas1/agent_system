"""tools.registry
Provides a simple global registry for tool instances so that they can be discovered
and reused across the application without creating tight coupling between
components.  Tools are stored by a lowercase string key and can be retrieved by
other parts of the system (e.g., ChatSession) when needed.

This initial implementation keeps the public surface minimal – just enough for
`ShellCommandTool` (and any future tools) to self-register.  It can be expanded
later to support namespacing, dynamic loading, or per-session overrides.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from threading import Lock

from .base import Tool  # Local import keeps dependency footprint small


class ToolRegistry:
    """A very small global registry for Tool instances."""

    _tools: Dict[str, Tool] = {}
    _lock: Lock = Lock()

    @classmethod
    def register(cls, name: str, tool: Tool) -> None:
        """Register a tool instance under *name*.

        If a tool is already registered under the same name it will be silently
        replaced.  Callers should therefore choose unique, descriptive names
        (e.g. ``"file_manager"`` or ``"shell_command"``).
        """
        # Normalise name for consistent look-ups.
        key = name.lower().strip()
        with cls._lock:
            cls._tools[key] = tool

    @classmethod
    def get(cls, name: str) -> Optional[Tool]:
        """Retrieve a tool by *name* or *None* if it is not present."""
        return cls._tools.get(name.lower().strip())

    @classmethod
    def list_tools(cls) -> List[str]:
        """Return a list of all registered tool names (sorted alphabetically)."""
        return sorted(cls._tools.keys()) 