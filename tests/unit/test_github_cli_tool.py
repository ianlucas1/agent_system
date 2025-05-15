"""Unit tests for GitHubCLITool (safe mock)."""
from __future__ import annotations

import subprocess

import pytest

from src.tools.github_cli import GitHubCLITool
from src.tools.base import ToolInput


def _exec(tool: GitHubCLITool, tool_name: str, args: str):
    return tool.execute(ToolInput("run", args={"tool": tool_name, "args": args}))


@pytest.fixture()
def cli_tool():
    return GitHubCLITool()


def test_git_status(monkeypatch, cli_tool):
    def fake_run(cmd, **kwargs):  # noqa: D401
        class R:
            returncode = 0
            stdout = "On branch main"
            stderr = ""
        return R()
    monkeypatch.setattr(subprocess, "run", fake_run)
    res = _exec(cli_tool, "git", "status")
    assert res.success and "On branch" in res.message


def test_git_push_blocked(cli_tool):
    res = _exec(cli_tool, "git", "push origin main")
    assert not res.success and ("blocked" in res.error or "not allowed" in res.error)


def test_gh_pr_list(monkeypatch, cli_tool):
    def fake_run(cmd, **kwargs):
        class R:
            returncode = 0
            stdout = "123  feat"  # sample
            stderr = ""
        return R()
    monkeypatch.setattr(subprocess, "run", fake_run)
    res = _exec(cli_tool, "gh", "pr list")
    assert res.success and "123" in res.message


def test_timeout(monkeypatch, cli_tool):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd="gh", timeout=8)
    monkeypatch.setattr(subprocess, "run", fake_run)
    res = _exec(cli_tool, "gh", "pr list")
    assert not res.success and "timed out" in res.error 