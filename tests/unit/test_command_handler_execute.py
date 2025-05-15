import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.handlers.command import CommandHandler, Command, CommandType
from src.tools.base import ToolOutput, ToolInput
from src.core.chat_session import ChatSession


class DummyFileTool:
    """A stub file tool we can program for each test."""

    def __init__(self, outputs):
        # outputs is a dict mapping operation_name -> ToolOutput
        self.outputs = outputs
        self.calls = []

    def execute(self, tool_input: ToolInput) -> ToolOutput:
        self.calls.append(tool_input)
        return self.outputs.get(tool_input.operation_name)


def _make_output(success, message="", data=None, error=""):
    return ToolOutput(success=success, message=message, data=data or {}, error=error or None)


def test_execute_read(monkeypatch):
    read_output = _make_output(True, message="content of file")
    dummy_tool = DummyFileTool({"read": read_output})
    handler = CommandHandler(file_tool=dummy_tool)

    cmd = Command(CommandType.READ, args="foo.txt")
    chat = ChatSession()
    # Directly call execute_command to isolate this logic
    resp = handler.execute_command(cmd, chat, "/read foo.txt")
    assert resp == "content of file"
    assert dummy_tool.calls[0].operation_name == "read"


def test_execute_write_requires_overwrite(monkeypatch):
    # First call returns overwrite required
    warn_output = _make_output(
        False,
        message="⚠️ File `foo.txt` already exists.",
        data={"status": "overwrite_required", "filename": "foo.txt"},
    )
    dummy_tool = DummyFileTool({"write": warn_output})
    handler = CommandHandler(file_tool=dummy_tool)
    chat = ChatSession()

    cmd = Command(CommandType.WRITE, args=("tmp_tests/foo.txt", "hello"))
    resp = handler.execute_command(cmd, chat, "/write tmp_tests/foo.txt hello")
    assert "already exists" in resp.lower()
    # Pending state set
    assert chat.pending_write_user_path == "tmp_tests/foo.txt"
    assert chat.pending_write_content == "hello"


def test_execute_overwrite_success(monkeypatch):
    success_output = _make_output(True, message="✅ Saved")
    dummy_tool = DummyFileTool({"write": success_output})
    handler = CommandHandler(file_tool=dummy_tool)
    chat = ChatSession()
    # set pending
    chat.pending_write_user_path = "tmp_tests/foo.txt"
    chat.pending_write_content = "hello"

    cmd = Command(CommandType.OVERWRITE, args="foo.txt")
    resp = handler.execute_command(cmd, chat, "/overwrite foo.txt")
    assert "saved" in resp.lower()
    assert chat.pending_write_user_path is None


def test_execute_overwrite_mismatch(monkeypatch):
    dummy_tool = DummyFileTool({"write": _make_output(True, message="should not be used")})
    handler = CommandHandler(file_tool=dummy_tool)
    chat = ChatSession()
    chat.pending_write_user_path = "tmp_tests/foo.txt"
    chat.pending_write_content = "abc"

    cmd = Command(CommandType.OVERWRITE, args="bar.txt")
    resp = handler.execute_command(cmd, chat, "/overwrite bar.txt")
    assert "no pending overwrite" in resp.lower()
    # Pending still there
    assert chat.pending_write_user_path is not None 