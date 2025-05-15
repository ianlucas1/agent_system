import os
import sys

# Add the project root to sys.path for src-based imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.core.chat_session import ChatSession


def test_system_prompt_in_history():
    cs = ChatSession()
    # System prompt should be the first message in history
    assert cs.history.messages[0].role == 'system'
    assert 'helpful AI assistant' in cs.history.messages[0].content

def test_add_and_clear_message_history():
    cs = ChatSession()
    cs.history.add_message('user', 'hello', 'user')
    cs.history.add_message('assistant', 'hi', 'openai')
    assert len(cs.history.messages) == 3  # system + 2
    cs.history.clear_chat(cs.system_prompt)
    assert len(cs.history.messages) == 1
    assert cs.history.messages[0].role == 'system'

def test_pending_write_logic():
    cs = ChatSession()
    cs.pending_write_user_path = 'foo.txt'
    cs.pending_write_content = 'bar'
    # Monkeypatch file_tool.execute to simulate a successful write
    cs.file_tool.execute = lambda tool_input: type('FakeOutput', (), {'success': True, 'message': '✅ Saved', 'error': None})()
    sender, response = cs.confirm_overwrite()
    assert 'Saved' in response
    assert cs.pending_write_user_path is None
    assert cs.pending_write_content is None 