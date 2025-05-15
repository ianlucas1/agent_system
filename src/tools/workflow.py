"""tools.workflow

Provides WorkflowTool to orchestrate a Planner → Coder → Reviewer cycle.
"""
from __future__ import annotations

import re
from typing import Any, Dict
import os

from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry
from src.shared.context_bus import ContextBus
from src.tools.multi_agent import MultiAgentTool
from src.shared.workspace import WorkspaceManager


class WorkflowTool(Tool):
    """Orchestrates Planner, Coder, and Reviewer agents for a given task."""

    def __init__(self, bus: ContextBus | None = None, multi_agent: MultiAgentTool | None = None) -> None:
        self.bus = bus or ContextBus()
        self.multi_agent = multi_agent or ToolRegistry.get("agent.multi") or MultiAgentTool()

    @staticmethod
    def _slugify(text: str) -> str:
        # Create a lowercase slug, replace non-alphanumeric with underscores, trim, limit length
        slug = re.sub(r"[^a-z0-9]+", "_", text.lower())
        slug = slug.strip("_")
        return slug[:30]

    def execute(self, tool_input: ToolInput) -> ToolOutput:
        args: Dict[str, Any] = tool_input.args or {}
        task = args.get("task")
        if not task or not isinstance(task, str):
            return ToolOutput(success=False, error="WorkflowTool: 'task' must be provided as a string.")
        context_key = args.get("context_key") or self._slugify(task)

        # Step 1: Planner
        planner_input = ToolInput("spawn", {
            "agent_name": "PlannerAgent",
            "role_prompt": "You are a software planner. Draft a step-by-step plan.",
            "task": task,
        })
        with WorkspaceManager.temp_dir("PlannerAgent") as tmp_dir:
            os.environ["WORKSPACE_TEMP"] = str(tmp_dir)
            plan_out = self.multi_agent.execute(planner_input)
        if not plan_out.success:
            return ToolOutput(success=False, error=f"PlannerAgent failed: {plan_out.error}")
        plan = plan_out.message or ""
        self.bus.set(f"{context_key}.plan", plan)

        # Step 2: Coder
        coder_input = ToolInput("spawn", {
            "agent_name": "CoderAgent",
            "role_prompt": "You are a senior Python coder. Produce code for the plan.",
            "task": plan,
        })
        with WorkspaceManager.temp_dir("CoderAgent") as tmp_dir:
            os.environ["WORKSPACE_TEMP"] = str(tmp_dir)
            code_out = self.multi_agent.execute(coder_input)
        if not code_out.success:
            return ToolOutput(success=False, error=f"CoderAgent failed: {code_out.error}")
        code = code_out.message or ""
        self.bus.set(f"{context_key}.code", code)

        # Step 3: Reviewer
        review_prompt = f"Please review the following plan and code.\nPlan:\n{plan}\n\nCode:\n{code}"
        reviewer_input = ToolInput("spawn", {
            "agent_name": "ReviewerAgent",
            "role_prompt": "You are a code reviewer. Ensure style, tests, and quality gates.",
            "task": review_prompt,
        })
        with WorkspaceManager.temp_dir("ReviewerAgent") as tmp_dir:
            os.environ["WORKSPACE_TEMP"] = str(tmp_dir)
            review_out = self.multi_agent.execute(reviewer_input)
        if not review_out.success:
            return ToolOutput(success=False, error=f"ReviewerAgent failed: {review_out.error}")
        review = review_out.message or ""
        self.bus.set(f"{context_key}.review", review)

        # Assemble report
        report = f"## Plan\n{plan}\n\n## Code\n{code}\n\n## Review\n{review}"
        return ToolOutput(success=True, message=report, data={"plan": plan, "code": code, "review": review})


# Register tool
ToolRegistry.register("workflow.pcr", WorkflowTool()) 