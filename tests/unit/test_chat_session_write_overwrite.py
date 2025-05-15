import os
import sys
from types import SimpleNamespace

# Add project root to import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.core.chat_session import ChatSession


def _make_tool_output(success: bool, message: str = "", error: str = "", data=None):
    return SimpleNamespace(success=success, message=message, error=error, data=data or {})


def test_write_overwrite_flow(monkeypatch):
    cs = ChatSession()

    # Prepare fake outputs
    overwrite_warning = _make_tool_output(
        False,
        message="⚠️ File `foo.txt` already exists. Please confirm overwrite or use a different filename.",
        data={"status": "overwrite_required", "filename": "foo.txt"},
    )
    success_output = _make_tool_output(True, message="✅ Saved", data={})

    calls = {
        "first": True
    }

    def fake_execute(tool_input):
        # First call returns overwrite warning, second returns success
        if calls["first"]:
            calls["first"] = False
            return overwrite_warning
        return success_output

    # Monkeypatch the file_tool.execute used by CommandHandler
    monkeypatch.setattr(cs.file_tool, "execute", fake_execute)

    # 1. Attempt to write without overwrite flag
    reply1 = cs.process_user_message("/write tmp_tests/foo.txt abc")
    assert any("overwrite" in msg.lower() for _sender, msg in reply1)
    assert cs.pending_write_user_path == "tmp_tests/foo.txt"
    assert cs.pending_write_content == "abc"

    # 2. Confirm overwrite
    reply2 = cs.process_user_message("/overwrite foo.txt")
    assert any("saved" in msg.lower() for _sender, msg in reply2)
    assert cs.pending_write_user_path is None
    assert cs.pending_write_content is None


def test_model_not_available(monkeypatch):
    cs = ChatSession()
    # Force OpenAI manager unavailable
    monkeypatch.setattr(cs.openai_manager, "_available", False)
    reply = cs.process_user_message("hello", model_choice="openai")
    assert any("not available" in msg.lower() for _sender, msg in reply) 