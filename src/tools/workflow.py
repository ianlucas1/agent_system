"""tools.workflow

Provides WorkflowTool to orchestrate a Planner → Coder → Reviewer cycle.
"""
from __future__ import annotations

import re
from typing import Any, Dict
import os
import json

from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry
from src.shared.context_bus import ContextBus
from src.tools.multi_agent import MultiAgentTool
from src.shared.workspace import WorkspaceManager
from src.tools.quality_gate import QualityGateTool


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
            err = f"PlannerAgent failed: {plan_out.error}"
            return ToolOutput(success=False, message=err, error=err)
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
            err = f"CoderAgent failed: {code_out.error}"
            return ToolOutput(success=False, message=err, error=err)
        code = code_out.message or ""
        self.bus.set(f"{context_key}.code", code)

        # Step 2.5: Quality Gate
        # Assume CoderAgent returns a JSON string: {"files": [["path", "content"]], ...}
        qa_status = ""
        qa_output = ""
        synced_files = []
        try:
            code_json = json.loads(code)
            patch = code_json.get("files")
            if not patch:
                raise ValueError("CoderAgent did not return a 'files' list.")
        except Exception as e:
            err = f"Failed to parse CoderAgent output as patch: {e}"
            return ToolOutput(success=False, message=err, error=err)

        # Get or register QualityGateTool
        qgate_tool = ToolRegistry.get("quality_gate")
        if not qgate_tool:
            qgate_tool = QualityGateTool(self.bus)
            ToolRegistry.register("quality_gate", qgate_tool)
        qgate_result = qgate_tool.call(agent_name="CoderAgent", patch=patch, message=f"Workflow: {context_key}")
        qa_status = qgate_result["status"]
        qa_output = qgate_result["qa_output"]
        synced_files = qgate_result["synced_files"]

        if qa_status != "PASS":
            # QA failed, skip ReviewerAgent
            report = f"## Plan\n{plan}\n\n## Code\n{code}\n\n## QA Status\n⚠️ QA failed.\n\n<details><summary>Show QA log</summary>\n\n{qa_output}\n</details>"
            return ToolOutput(success=False, message=report, data={"plan": plan, "code": code, "qa_output": qa_output, "qa_status": qa_status})

        # Step 3: Reviewer (only if QA passed)
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
            err = f"ReviewerAgent failed: {review_out.error}"
            return ToolOutput(success=False, message=err, error=err)
        review = review_out.message or ""
        self.bus.set(f"{context_key}.review", review)

        # Assemble report
        report = f"## Plan\n{plan}\n\n## Code\n{code}\n\n## QA Status\n✅ QA PASS\n\n<details><summary>Show QA log</summary>\n\n{qa_output}\n</details>\n\n## Review\n{review}"
        return ToolOutput(success=True, message=report, data={"plan": plan, "code": code, "qa_output": qa_output, "qa_status": qa_status, "review": review, "synced_files": synced_files})


# Register tool
ToolRegistry.register("workflow.pcr", WorkflowTool()) 