"""tools.multi_agent

MultiAgentTool – minimal A2A proof-of-concept.  Spawns a *single-turn* sub-agent
(a fresh ChatSession) with a role prompt and task, captures its first response
and optionally persists it to a shared context file.
"""
from __future__ import annotations

import logging
import os
from typing import Dict, Optional

from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry
from ..shared.metrics import MetricsManager

logger = logging.getLogger(__name__)

# Default location for agent output if caller does not specify a file.
_DEFAULT_CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "agent_workspace")

# Optional import for runtime; replaced in tests.
try:
    from src.core.chat_session import ChatSession as _RealChatSession  # noqa
except Exception:  # pragma: no cover – import may fail in test env w/o deps
    _RealChatSession = None  # type: ignore[misc,assignment]


class MultiAgentTool(Tool):
    """Spawn a subordinate ChatSession and return its single-turn reply."""

    def _write_context(self, content: str, filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.info("Sub-agent context saved to %s", filepath)

    # ------------------------------------------------------------------
    def execute(self, tool_input: ToolInput) -> ToolOutput:  # noqa: D401
        if tool_input.operation_name.lower() not in {"spawn", "run", "delegate"}:
            return ToolOutput(success=False, error="Unsupported operation for MultiAgentTool.")

        args: Dict[str, Optional[str]] = tool_input.args or {}
        name = args.get("agent_name") or "SubAgent"
        role_prompt = args.get("role_prompt") or "You are a helpful assistant."
        task = args.get("task")
        if not task:
            return ToolOutput(success=False, error="Task must be provided.")

        context_file = args.get("context_file")
        if not context_file:
            safe_name = name.lower().replace(" ", "_")
            context_file = os.path.join(_DEFAULT_CONTEXT_DIR, f"agent_{safe_name}.txt")

        # Resolve ChatSession implementation (real or monkey-patched in tests).
        ChatSessionCls = _RealChatSession  # may be None
        if ChatSessionCls is None:
            from src.core.chat_session import ChatSession as ChatSessionCls  # type: ignore

        logger.info("Spawning sub-agent '%s' for one-shot task", name)
        sub_session = ChatSessionCls()
        # Reset system prompt to role_prompt
        sub_session.history.clear_chat(role_prompt)
        # Run single turn
        responses = sub_session.process_user_message(task, model_choice="openai")
        if not responses:
            return ToolOutput(success=False, error="Sub-agent produced no response.")
        # Take first assistant reply content
        _sender, reply = responses[0]
        # Truncate to 700 tokens/approx chars (simple char limit)
        max_chars = 4000  # ~ 1000 tokens approx
        if len(reply) > max_chars:
            reply = reply[:max_chars] + "\n[...truncated...]"

        try:
            self._write_context(reply, context_file)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to write context file: %s", exc)
            return ToolOutput(success=False, error=f"Failed to write context: {exc}")
        # Record reply in shared context bus
        try:
            from src.shared.context_bus import ContextBus
            ContextBus().append(f"{name.lower().replace(' ', '_')}_log", reply)
        except Exception as exc:
            logger.error("Failed to append to ContextBus: %s", exc)
        summary = f"🧑‍🤝‍🧑 {name} responded and context saved to {context_file}"

        # Assuming each execution of MultiAgentTool counts as an agent spawned for metrics
        MetricsManager().agents_spawned_total.inc()

        return ToolOutput(success=True, message=summary, data={"reply": reply, "file": context_file})


# Register the tool globally
ToolRegistry.register("agent.multi", MultiAgentTool()) 