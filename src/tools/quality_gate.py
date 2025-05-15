import os
import shutil
import subprocess
from typing import Any, Dict, List, Tuple

from src.shared.context_bus import ContextBus
from src.shared.workspace import WorkspaceManager
from src.shared.apply_utils import apply_patch
from src.tools.base import Tool
from ..shared.metrics import MetricsManager


class QualityGateTool(Tool):
    """
    A tool to apply a code patch in a temporary workspace, run quality checks,
    and optionally sync the changes back to the main repository.
    """

    def __init__(self, context_bus: ContextBus):
        super().__init__()
        self._context_bus = context_bus

    @property
    def name(self) -> str:
        return "quality_gate"

    @property
    def description(self) -> str:
        return "Applies a code patch, runs quality checks (ruff, pytest, mypy, bandit), and syncs on pass."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "The name of the agent proposing the patch.",
                },
                "patch": {
                    "type": "array",
                    "description": "The code patch as a list of (relative_path, new_content) tuples.",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
                "message": {
                    "type": "string",
                    "description": "A brief message describing the patch.",
                },
            },
            "required": ["agent_name", "patch", "message"],
        }

    def call(self, **kwargs: Any) -> Dict[str, Any]:
        agent_name: str = kwargs["agent_name"]
        patch: List[Tuple[str, str]] = kwargs["patch"]
        message: str = kwargs["message"]

        qa_output = ""
        all_checks_passed = True
        changed_files = []

        with WorkspaceManager.temp_dir(agent_name) as tmp_dir:
            try:
                # 1. Temp apply patch
                changed_files = apply_patch(tmp_dir, patch)
                relative_changed_files = [os.path.relpath(f, tmp_dir) for f in changed_files] # Should already be relative, but just in case.

                # 2. Run checks (in tmp)
                checks = [
                    ("Ruff", ["ruff", "check", "."], True),  # Blocking
                    ("Pytest", ["pytest", "-q"], True), # Blocking (via pytest.ini coverage gate)
                    ("MyPy", ["mypy"] + relative_changed_files, False), # Non-blocking in CI, but blocking for gate
                    ("Bandit", ["bandit", "-q", "-r", "."], False), # Non-blocking in CI, but blocking for gate (running on tmp_dir)
                ]

                for check_name, command, is_blocking in checks:
                    print(f"Running {check_name} in {tmp_dir}...")
                    result = subprocess.run(
                        command,
                        cwd=tmp_dir,
                        capture_output=True,
                        text=True
                    )
                    qa_output += f"--- {check_name} ---\n"
                    qa_output += result.stdout
                    qa_output += result.stderr
                    qa_output += f"Exit Code: {result.returncode}\n\n"

                    if result.returncode != 0:
                        all_checks_passed = False
                        if is_blocking:
                            print(f"{check_name} failed (blocking). Stopping checks.")
                            break # Stop on first blocking failure
                        else:
                             print(f"{check_name} failed (non-blocking). Continuing checks.")

                # 3. Decision
                if all_checks_passed:
                    # 4. If all green, sync the patch into the real repo
                    print("All QA checks passed. Syncing changes to real repo.")
                    real_repo_root = os.getcwd() # Assuming tool is called from repo root
                    for rel_path in changed_files:
                         # Ensure target directory exists in the real repo
                        real_path = os.path.join(real_repo_root, rel_path)
                        os.makedirs(os.path.dirname(real_path), exist_ok=True)
                        shutil.copy2(os.path.join(tmp_dir, rel_path), real_path)
                    status = "PASS"
                    log_message = f"{agent_name}: PASS - {message}"
                    MetricsManager().qa_pass_total.inc()
                else:
                    # Otherwise return the failure log
                    print("QA checks failed. Changes not synced.")
                    status = "FAIL"
                    log_message = f"{agent_name}: FAIL - {message}"
                    MetricsManager().qa_fail_total.inc()

            except Exception as e:
                status = "ERROR"
                qa_output += f"An error occurred during QA checks: {e}\n"
                log_message = f"{agent_name}: ERROR - {message} ({e})"
                all_checks_passed = False # Ensure fail status on error
            finally:
                 # 4. ContextBus log (always log outcome)
                self._context_bus.append("quality_gate", log_message)

        return {
            "status": status,
            "qa_output": qa_output,
            "synced_files": changed_files if all_checks_passed else [],
            "all_checks_passed": all_checks_passed
        }

    def execute(self, tool_input):
        return self.call(**(tool_input.args or {})) 