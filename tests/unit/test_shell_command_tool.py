"""Unit tests for ShellCommandTool.

These tests use real subprocess calls so they are *integration-ish* but still
quick (each command finishes in < 1s).  They run against the local OS, therefore
avoid platform-specific assumptions as much as possible.
"""
from __future__ import annotations

import sys

import pytest

from src.tools.shell_command import ShellCommandTool
from src.tools.base import ToolInput


@pytest.fixture()
def tool() -> ShellCommandTool:  # noqa: D401 – simple fixture
    return ShellCommandTool()


def _run(tool: ShellCommandTool, cmd: str):
    return tool.execute(ToolInput("run", {"command": cmd}))


def test_basic_echo(tool):
    result = _run(tool, "echo hello")
    assert result.success is True
    assert "hello" in (result.message or "")


def test_command_not_found(tool):
    # Use a *very* unlikely command name to trigger a not-found error regardless of platform.
    result = _run(tool, "cmd_does_not_exist_12345")
    assert result.success is False
    assert result.error is not None


def test_timeout(tool):
    # Cross-platform way to sleep: use Python itself (available) so we are not dependent on /bin/sleep on Windows.
    result = _run(tool, f"{sys.executable} -c \"import time; time.sleep(10)\"")
    assert result.success is False
    assert "timed out" in (result.error or result.message or "")


def test_output_truncation(tool):
    # Generate 500 lines quickly using Python – platform-independent.
    cmd = (
        f"{sys.executable} -c \"[print(i) for i in range(1, 501)]\""
    )
    result = _run(tool, cmd)
    assert result.success is True
    # The message should contain the truncation marker because only 200 lines are kept.
    assert "output truncated" in (result.message or "")


def test_restricted_command(tool):
    result = _run(tool, "rm -rf /")
    assert result.success is False
    assert "blocked" in (result.error or result.message or "") 