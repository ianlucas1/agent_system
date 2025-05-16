import os
import sys
import pytest

# Add the project root to sys.path for src-based imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.core.chat_session import ChatSession

@pytest.mark.skip(reason="Test fails in CI due to missing API keys; needs proper mocking or to be run in envs with keys.")
def test_basic_flow(monkeypatch):
    cs = ChatSession()
    # Monkeypatch the OpenAI manager's generate_response method to return a fixed string
    monkeypatch.setattr(cs.openai_manager, 'generate_response', lambda *_: 'pong')
    reply = cs.process_user_message('ping')
    # process_user_message returns a list of (sender, content) tuples
    assert any('pong' in content.lower() for _, content in reply) 