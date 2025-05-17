"""Smoke-tests to ensure key modules import and tools are discoverable.
The goal is to catch bad import paths or missing dependencies early in CI.
"""
import importlib

import pytest
from src.tools.registry import ToolRegistry

# --- 1. Critical module import list ---
CRITICAL_MODULES = [
    "src.interfaces.app",
    "src.core.chat_session",
    "src.handlers.command",
    "src.tools.memory",
    "src.tools.registry",
]


@pytest.mark.parametrize("module_name", CRITICAL_MODULES)
def test_module_imports(module_name):
    """Ensure each critical module can be imported without errors."""
    importlib.import_module(module_name)


# --- 2. Tool Registry sanity ---
def test_tool_registry_integrity():
    """All registered tools should be importable and expose an execute method."""
    registry_contents = ToolRegistry.list_tools()
    assert registry_contents, "ToolRegistry should not be empty"
    for name in registry_contents:
        tool = ToolRegistry.get(name)
        # Tool instance should exist and have callable execute
        assert tool is not None, f"Tool '{name}' could not be instantiated"
        assert callable(getattr(tool, "execute", None)), f"Tool '{name}' missing execute()" 