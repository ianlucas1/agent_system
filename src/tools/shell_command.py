"""tools.shell_command

Provides ``ShellCommandTool`` – a backend utility that allows the agent to run
shell commands in the *workspace root* using :pyfunc:`subprocess.run`.  The tool
applies several safety features to make execution reasonably safe when driven
by an LLM:

* A short timeout (default **5 seconds**) prevents long-running or blocking
  commands.
* Stderr is captured but only returned if the command fails; otherwise it is
  suppressed to keep output noise low.
* Output is truncated to **200 lines** to avoid runaway responses.
* A small deny-list blocks obviously dangerous commands (e.g. `rm -rf /`).

The tool can be invoked through ``ToolInput`` like so::

    tool = ShellCommandTool()
    result = tool.execute(ToolInput("run", {"command": "echo 'hello'"}))
    print(result.message)  # -> "hello"

The class self-registers under the key ``"shell_command"`` in
:pydata:`src.tools.registry.ToolRegistry`, making it discoverable by other
components such as :pyclass:`src.core.chat_session.ChatSession`.
"""
from __future__ import annotations

import logging
import subprocess
import textwrap
from typing import List

from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


class ShellCommandTool(Tool):
    """Execute *safe* shell commands inside the local project directory."""

    # Reasonable defaults – kept class-level for easier later configuration.
    DEFAULT_TIMEOUT_SECONDS: int = 5
    MAX_OUTPUT_LINES: int = 200

    # Very small deny list – this can be made configurable later.
    _DANGEROUS_TOKENS: List[str] = [
        "rm -rf",
        "rm -r /",
        "shutdown",
        "poweroff",
        "reboot",
        "halt",
        "mkfs",
        "dd ",  # leading space avoids matching words like 'address'
        ":(){:|:&};:",  # fork bomb
        "kill -9",
        "killall",
        "sudo ",
    ]

    def _is_dangerous(self, cmd: str) -> bool:
        cmd_lower = cmd.lower()
        return any(token in cmd_lower for token in self._DANGEROUS_TOKENS)

    def _truncate_output(self, output: str) -> str:
        lines = output.splitlines()
        if len(lines) <= self.MAX_OUTPUT_LINES:
            return output
        truncated = "\n".join(lines[: self.MAX_OUTPUT_LINES])
        return f"{truncated}\n[...output truncated after {self.MAX_OUTPUT_LINES} lines...]"

    # ---------------------------------------------------------------------
    # Public API – part of the Tool interface
    # ---------------------------------------------------------------------
    def execute(self, tool_input: ToolInput) -> ToolOutput:  # noqa: D401 – simple method
        """Run a shell command provided in *tool_input*.

        Expected ``tool_input`` structure::

            ToolInput(
                operation_name="run",  # or "execute", "cli"
                args={"command": "git status"}
            )
        """
        op = tool_input.operation_name.lower().strip()
        if op not in {"run", "execute", "cli"}:
            return ToolOutput(
                success=False,
                error=f"Unsupported operation for ShellCommandTool: {tool_input.operation_name}",
            )

        raw_cmd = tool_input.args.get("command") if tool_input.args else None
        if not raw_cmd or not isinstance(raw_cmd, str):
            return ToolOutput(success=False, error="No command provided to execute.")

        # Safety check ----------------------------------------------------
        if self._is_dangerous(raw_cmd):
            logger.warning("Blocked dangerous command: %s", raw_cmd)
            return ToolOutput(
                success=False,
                error="⚠️ Dangerous command detected and blocked.",
                message=f"Command '{raw_cmd}' was blocked for safety.",
            )

        logger.info("Executing shell command: %s", raw_cmd)

        try:
            # We purposely run through the shell to allow simple commands like
            # "echo 'hello world'" without needing to parse quoting properly.
            completed = subprocess.run(
                raw_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.DEFAULT_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            logger.warning("Command timed out after %s seconds: %s", self.DEFAULT_TIMEOUT_SECONDS, raw_cmd)
            return ToolOutput(success=False, error="⏰ Command timed out after 5 seconds.")
        except Exception as exc:  # Broad except is okay for tool boundary.
            logger.exception("Exception while executing shell command: %s", raw_cmd)
            return ToolOutput(success=False, error=f"⚠️ Error while executing command: {exc}")

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        # Truncate output early to avoid needless memory / log pressure.
        stdout = self._truncate_output(stdout)
        stderr = self._truncate_output(stderr)

        if completed.returncode != 0:
            logger.warning(
                "Command returned non-zero exit code %s: %s", completed.returncode, raw_cmd
            )
            combined = stderr or stdout or f"(exit code {completed.returncode})"
            # Indent to distinguish error text.
            formatted = textwrap.indent(combined, "    ")
            return ToolOutput(
                success=False,
                message=f"⚠️ Command exited with code {completed.returncode}\n```\n{formatted}\n```",
                error=combined,
                data={
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": completed.returncode,
                },
            )

        # Success path ----------------------------------------------------
        # If caller explicitly asked for stderr we could add it later – for now we ignore it.
        if not stdout:
            stdout = "(no output)"
        # Wrap in code fence for nicer display.
        wrapped_output = f"```shell\n{stdout}\n```"
        return ToolOutput(success=True, message=wrapped_output, data={"stdout": stdout})


# -------------------------------------------------------------------------
# Auto-registration – make the tool discoverable system-wide.
# -------------------------------------------------------------------------
ToolRegistry.register("shell_command", ShellCommandTool()) 