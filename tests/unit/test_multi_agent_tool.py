"""Tests for MultiAgentTool.

We patch the ChatSession used by the tool so that no external API calls are made.
"""
from __future__ import annotations

import os
from typing import List, Tuple

import pytest

from src.tools.multi_agent import MultiAgentTool
from src.tools.base import ToolInput


class DummyChatSession:  # noqa: D401 – simple stub
    """Minimal stub mimicking ChatSession public API used by MultiAgentTool."""

    def __init__(self):
        self.history = self

    # --- history subset ---
    def clear_chat(self, system_prompt_content: str):  # noqa: D401
        # store but otherwise ignore
        self._sys = system_prompt_content

    # --- main API ---
    def process_user_message(
        self,
        user_input: str,
        model_choice: str = "openai",
        specific_model_name: str | None = None,
        use_a2a: bool = False,
    ) -> List[Tuple[str, str]]:
        # Echo stub response
        return [("openai", f"ECHO:{user_input}")]


@pytest.fixture(autouse=True)
def patch_chatsession(monkeypatch):  # noqa: D401
    """Patch ChatSession inside the tool module."""

    from src.tools import multi_agent as ma

    monkeypatch.setattr(ma, "_RealChatSession", DummyChatSession, raising=False)
    yield


def _run(tool: MultiAgentTool, **kwargs):
    inp = ToolInput("spawn", args=kwargs)
    return tool.execute(inp)


def test_basic_spawn(tmp_path):
    tool = MultiAgentTool()
    ctx_file = tmp_path / "planner.md"
    res = _run(
        tool,
        agent_name="PlannerAgent",
        role_prompt="You plan",
        task="Write outline",
        context_file=str(ctx_file),
    )
    assert res.success
    assert ctx_file.exists()
    content = ctx_file.read_text()
    assert "ECHO:Write outline" in content


def test_default_context_file(tmp_path, monkeypatch):
    # Patch workspace dir
    monkeypatch.chdir(tmp_path)
    tool = MultiAgentTool()
    res = _run(tool, task="Do something")
    assert res.success
    file_path = res.data["file"]
    assert os.path.exists(file_path)


def test_missing_task():
    tool = MultiAgentTool()
    res = _run(tool)
    assert not res.success
    assert "Task must be provided" in res.error 