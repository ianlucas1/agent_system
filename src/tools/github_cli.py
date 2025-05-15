"""tools.github_cli

Git and GitHub CLI wrapper allowing safe read-only commands from chat.
"""
from __future__ import annotations

import logging
import shlex
import subprocess
from typing import List

from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry
from ..shared.metrics import MetricsManager

logger = logging.getLogger(__name__)

_ALLOWED_GIT = {
    "status",
    "branch",
    "checkout",
    "diff",
    "log",
}
_ALLOWED_GH = {
    "pr",
}

_BLOCKED_TOKENS = {"push", "rm", "reset", "rebase", "force", "!"}

_MAX_LINES = 400
_TIMEOUT = 8  # seconds


class GitHubCLITool(Tool):
    """Execute whitelisted `git` or `gh` commands with guardrails."""

    def _is_safe(self, cmd_parts: List[str]) -> bool:
        for tok in cmd_parts:
            if tok in _BLOCKED_TOKENS:
                return False
        return True

    def _truncate(self, text: str) -> str:
        lines = text.splitlines()
        if len(lines) <= _MAX_LINES:
            return text
        return "\n".join(lines[:_MAX_LINES]) + f"\n[...truncated after {_MAX_LINES} lines...]"

    # -----------------------------------------------------------------
    def execute(self, tool_input: ToolInput) -> ToolOutput:  # noqa: D401
        MetricsManager().cli_calls_total.inc()
        payload = tool_input.args or {}
        tool = payload.get("tool")
        args_str = payload.get("args", "")
        if tool not in {"git", "gh"}:
            return ToolOutput(success=False, error="tool must be 'git' or 'gh'")
        try:
            parts = shlex.split(args_str)
        except ValueError as exc:
            return ToolOutput(success=False, error=f"Arg parse error: {exc}")
        if not parts:
            return ToolOutput(success=False, error="No sub-command provided.")

        sub_cmd = parts[0]
        allowed = _ALLOWED_GIT if tool == "git" else _ALLOWED_GH
        if sub_cmd not in allowed:
            return ToolOutput(success=False, error=f"Sub-command '{sub_cmd}' not allowed.")
        if not self._is_safe(parts):
            logger.warning("Blocked destructive %s command: %s", tool, args_str)
            return ToolOutput(success=False, error="⚠️ destructive op blocked")

        full_cmd = [tool, *parts]
        logger.info("Executing %s command: %s", tool, " ".join(full_cmd))
        try:
            completed = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warning("%s command timed out", tool)
            return ToolOutput(success=False, error="⏰ command timed out")
        except Exception as exc:  # noqa: BLE001
            logger.exception("%s command error", tool)
            return ToolOutput(success=False, error=str(exc))

        out_text = completed.stdout or completed.stderr or "(no output)"
        out_text = self._truncate(out_text.strip())
        fenced = f"```shell\n{out_text}\n```"
        if completed.returncode != 0:
            return ToolOutput(success=False, message=f"⚠️ exit {completed.returncode}\n{fenced}")
        return ToolOutput(success=True, message=fenced)


# Register under both IDs
ToolRegistry.register("vcs.git", GitHubCLITool())
ToolRegistry.register("vcs.gh", GitHubCLITool()) 