import os
import unittest
from unittest.mock import MagicMock, patch

from src.shared.context_bus import ContextBus
from src.tools.quality_gate import QualityGateTool


class TestQualityGateTool(unittest.TestCase):

    def setUp(self):
        self.mock_context_bus = MagicMock(spec=ContextBus)
        self.quality_gate_tool = QualityGateTool(context_bus=self.mock_context_bus)
        self.agent_name = "TestAgent"
        self.patch = [("test_file.py", "print('hello')")]
        self.message = "Add test_file.py"
        self.mock_tmp_dir = "/fake/temp/dir"

    @patch('src.tools.quality_gate.apply_patch')
    @patch('src.tools.quality_gate.subprocess.run')
    @patch('src.tools.quality_gate.shutil.copy2')
    @patch('src.tools.quality_gate.os.makedirs')
    @patch('src.tools.quality_gate.os.getcwd', return_value='/fake/repo/root')
    @patch('src.tools.quality_gate.WorkspaceManager.temp_dir')
    def test_quality_gate_pass(self, mock_temp_dir, mock_getcwd, mock_makedirs, mock_copy2, mock_subprocess_run, mock_apply_patch):
        # Mock WorkspaceManager.temp_dir to return a fixed temporary directory
        mock_temp_dir.return_value.__enter__.return_value = self.mock_tmp_dir
        mock_temp_dir.return_value.__exit__.return_value = None

        # Mock apply_patch to indicate successful application and return changed files
        mock_apply_patch.return_value = ["test_file.py"]

        # Mock subprocess.run for all checks to pass
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Call the tool
        result = self.quality_gate_tool.call(
            agent_name=self.agent_name,
            patch=self.patch,
            message=self.message
        )

        # Assertions
        self.assertTrue(result["all_checks_passed"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["synced_files"], ["test_file.py"])
        mock_apply_patch.assert_called_once_with(self.mock_tmp_dir, self.patch)
        mock_subprocess_run.call_count = 4 # Ruff, Pytest, MyPy, Bandit
        mock_makedirs.assert_called_once_with('/fake/repo/root', exist_ok=True)
        mock_copy2.assert_called_once_with(os.path.join(self.mock_tmp_dir, "test_file.py"), os.path.join("/fake/repo/root", "test_file.py"))
        self.mock_context_bus.append.assert_called_once_with("quality_gate", f"{self.agent_name}: PASS - {self.message}")

    @patch('src.tools.quality_gate.apply_patch')
    @patch('src.tools.quality_gate.subprocess.run')
    @patch('src.tools.quality_gate.shutil.copy2')
    @patch('src.tools.quality_gate.os.makedirs')
    @patch('src.tools.quality_gate.os.getcwd', return_value='/fake/repo/root')
    @patch('src.tools.quality_gate.WorkspaceManager.temp_dir')
    def test_quality_gate_ruff_fail(self, mock_temp_dir, mock_getcwd, mock_makedirs, mock_copy2, mock_subprocess_run, mock_apply_patch):
        mock_temp_dir.return_value.__enter__.return_value = self.mock_tmp_dir
        mock_temp_dir.return_value.__exit__.return_value = None
        mock_apply_patch.return_value = ["test_file.py"]

        # Mock subprocess.run to fail Ruff
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=1, stdout="Ruff errors", stderr=""), # Ruff fails
            MagicMock(returncode=0, stdout="", stderr=""), # Pytest passes (not called due to early exit)
            MagicMock(returncode=0, stdout="", stderr=""), # MyPy passes (not called)
            MagicMock(returncode=0, stdout="", stderr="")  # Bandit passes (not called)
        ]

        result = self.quality_gate_tool.call(
            agent_name=self.agent_name,
            patch=self.patch,
            message=self.message
        )

        self.assertFalse(result["all_checks_passed"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["synced_files"], [])
        self.assertIn("--- Ruff ---", result["qa_output"])
        self.assertIn("Exit Code: 1", result["qa_output"])
        mock_apply_patch.assert_called_once_with(self.mock_tmp_dir, self.patch)
        mock_subprocess_run.call_count = 1 # Only Ruff should be called
        mock_copy2.assert_not_called()
        self.mock_context_bus.append.assert_called_once_with("quality_gate", f"{self.agent_name}: FAIL - {self.message}")

    @patch('src.tools.quality_gate.apply_patch')
    @patch('src.tools.quality_gate.subprocess.run')
    @patch('src.tools.quality_gate.shutil.copy2')
    @patch('src.tools.quality_gate.os.makedirs')
    @patch('src.tools.quality_gate.os.getcwd', return_value='/fake/repo/root')
    @patch('src.tools.quality_gate.WorkspaceManager.temp_dir')
    def test_quality_gate_pytest_fail(self, mock_temp_dir, mock_getcwd, mock_makedirs, mock_copy2, mock_subprocess_run, mock_apply_patch):
        mock_temp_dir.return_value.__enter__.return_value = self.mock_tmp_dir
        mock_temp_dir.return_value.__exit__.return_value = None
        mock_apply_patch.return_value = ["test_file.py"]

        # Mock subprocess.run to pass Ruff, fail Pytest
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # Ruff passes
            MagicMock(returncode=1, stdout="Pytest errors", stderr=""), # Pytest fails
            MagicMock(returncode=0, stdout="", stderr=""), # MyPy passes (not called)
            MagicMock(returncode=0, stdout="", stderr="")  # Bandit passes (not called)
        ]

        result = self.quality_gate_tool.call(
            agent_name=self.agent_name,
            patch=self.patch,
            message=self.message
        )

        self.assertFalse(result["all_checks_passed"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["synced_files"], [])
        self.assertIn("--- Pytest ---", result["qa_output"])
        self.assertIn("Exit Code: 1", result["qa_output"])
        mock_apply_patch.assert_called_once_with(self.mock_tmp_dir, self.patch)
        mock_subprocess_run.call_count = 2 # Ruff and Pytest called
        mock_copy2.assert_not_called()
        self.mock_context_bus.append.assert_called_once_with("quality_gate", f"{self.agent_name}: FAIL - {self.message}")

    @patch('src.tools.quality_gate.apply_patch')
    @patch('src.tools.quality_gate.subprocess.run')
    @patch('src.tools.quality_gate.shutil.copy2')
    @patch('src.tools.quality_gate.os.makedirs')
    @patch('src.tools.quality_gate.os.getcwd', return_value='/fake/repo/root')
    @patch('src.tools.quality_gate.WorkspaceManager.temp_dir')
    def test_quality_gate_mypy_fail(self, mock_temp_dir, mock_getcwd, mock_makedirs, mock_copy2, mock_subprocess_run, mock_apply_patch):
        mock_temp_dir.return_value.__enter__.return_value = self.mock_tmp_dir
        mock_temp_dir.return_value.__exit__.return_value = None
        mock_apply_patch.return_value = ["test_file.py"]

        # Mock subprocess.run to pass Ruff, Pytest, fail MyPy
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # Ruff passes
            MagicMock(returncode=0, stdout="", stderr=""), # Pytest passes
            MagicMock(returncode=1, stdout="MyPy errors", stderr=""), # MyPy fails
            MagicMock(returncode=0, stdout="", stderr="")  # Bandit passes (not called)
        ]

        result = self.quality_gate_tool.call(
            agent_name=self.agent_name,
            patch=self.patch,
            message=self.message
        )

        self.assertFalse(result["all_checks_passed"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["synced_files"], [])
        self.assertIn("--- MyPy ---", result["qa_output"])
        self.assertIn("Exit Code: 1", result["qa_output"])
        mock_apply_patch.assert_called_once_with(self.mock_tmp_dir, self.patch)
        mock_subprocess_run.call_count = 3 # Ruff, Pytest, MyPy called
        mock_copy2.assert_not_called()
        self.mock_context_bus.append.assert_called_once_with("quality_gate", f"{self.agent_name}: FAIL - {self.message}")

    @patch('src.tools.quality_gate.apply_patch')
    @patch('src.tools.quality_gate.subprocess.run')
    @patch('src.tools.quality_gate.shutil.copy2')
    @patch('src.tools.quality_gate.os.makedirs')
    @patch('src.tools.quality_gate.os.getcwd', return_value='/fake/repo/root')
    @patch('src.tools.quality_gate.WorkspaceManager.temp_dir')
    def test_quality_gate_bandit_fail(self, mock_temp_dir, mock_getcwd, mock_makedirs, mock_copy2, mock_subprocess_run, mock_apply_patch):
        mock_temp_dir.return_value.__enter__.return_value = self.mock_tmp_dir
        mock_temp_dir.return_value.__exit__.return_value = None
        mock_apply_patch.return_value = ["test_file.py"]

        # Mock subprocess.run to pass Ruff, Pytest, MyPy, fail Bandit
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # Ruff passes
            MagicMock(returncode=0, stdout="", stderr=""), # Pytest passes
            MagicMock(returncode=0, stdout="", stderr=""), # MyPy passes
            MagicMock(returncode=1, stdout="Bandit errors", stderr="") # Bandit fails
        ]

        result = self.quality_gate_tool.call(
            agent_name=self.agent_name,
            patch=self.patch,
            message=self.message
        )

        self.assertFalse(result["all_checks_passed"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["synced_files"], [])
        self.assertIn("--- Bandit ---", result["qa_output"])
        self.assertIn("Exit Code: 1", result["qa_output"])
        mock_apply_patch.assert_called_once_with(self.mock_tmp_dir, self.patch)
        mock_subprocess_run.call_count = 4 # Ruff, Pytest, MyPy, Bandit called
        mock_copy2.assert_not_called()
        self.mock_context_bus.append.assert_called_once_with("quality_gate", f"{self.agent_name}: FAIL - {self.message}") 