import unittest
from unittest.mock import patch, MagicMock
from src.tools.workflow import WorkflowTool
from src.shared.context_bus import ContextBus
from src.tools.multi_agent import MultiAgentTool
from src.tools.base import ToolInput, ToolOutput

class TestWorkflowToolQualityGate(unittest.TestCase):
    def setUp(self):
        self.bus = ContextBus()
        self.mock_multi_agent = MagicMock(spec=MultiAgentTool)
        self.workflow = WorkflowTool(bus=self.bus, multi_agent=self.mock_multi_agent)

    @patch('src.tools.workflow.ToolRegistry')
    def test_workflow_qagate_pass(self, mock_registry):
        # Mock PlannerAgent output
        self.mock_multi_agent.execute.side_effect = [
            ToolOutput(success=True, message="Step 1: Do X"),
            # CoderAgent returns JSON with files
            ToolOutput(success=True, message='{"files": [["foo.py", "print(1)\\n"]]}'),
            ToolOutput(success=True, message="LGTM!") # ReviewerAgent
        ]
        # Mock QualityGateTool to PASS
        mock_qgate = MagicMock()
        mock_qgate.call.return_value = {
            "status": "PASS",
            "qa_output": "All checks passed.",
            "synced_files": ["foo.py"],
            "all_checks_passed": True
        }
        mock_registry.get.return_value = mock_qgate

        tool_input = ToolInput("workflow.pcr", {"task": "Add foo.py"})
        result = self.workflow.execute(tool_input)
        self.assertTrue(result.success)
        self.assertIn("QA PASS", result.message)
        self.assertIn("LGTM", result.message)
        self.assertIn("foo.py", str(result.data["synced_files"]))
        self.assertEqual(self.mock_multi_agent.execute.call_count, 3) # Planner, Coder, Reviewer
        mock_qgate.call.assert_called_once()

    @patch('src.tools.workflow.ToolRegistry')
    def test_workflow_qagate_fail(self, mock_registry):
        # Mock PlannerAgent output
        self.mock_multi_agent.execute.side_effect = [
            ToolOutput(success=True, message="Step 1: Do X"),
            # CoderAgent returns JSON with files
            ToolOutput(success=True, message='{"files": [["foo.py", "print(1)\\n"]]}'),
        ]
        # Mock QualityGateTool to FAIL
        mock_qgate = MagicMock()
        mock_qgate.call.return_value = {
            "status": "FAIL",
            "qa_output": "Ruff failed.",
            "synced_files": [],
            "all_checks_passed": False
        }
        mock_registry.get.return_value = mock_qgate

        tool_input = ToolInput("workflow.pcr", {"task": "Add foo.py"})
        result = self.workflow.execute(tool_input)
        self.assertFalse(result.success)
        self.assertIn("QA failed", result.message)
        self.assertIn("Ruff failed", result.message)
        self.assertEqual(self.mock_multi_agent.execute.call_count, 2) # Planner, Coder only
        mock_qgate.call.assert_called_once() 