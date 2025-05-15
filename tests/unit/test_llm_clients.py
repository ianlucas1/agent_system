import os
import sys

# Add the project root to sys.path for src-based imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.llm import clients as llm_clients


def test_openai_manager_no_api_key():
    mgr = llm_clients.OpenAIClientManager(api_key=None, default_model_name="dummy")
    assert not mgr.available
    resp = mgr.generate_response([])
    assert "not available" in resp


def test_openai_count_tokens_without_tiktoken(monkeypatch):
    mgr = llm_clients.OpenAIClientManager(api_key=None, default_model_name="dummy")
    # Ensure fallback path by monkeypatching tiktoken availability flags
    monkeypatch.setattr(llm_clients, "TIKTOKEN_AVAILABLE", False)
    # Also ensure manager reports unavailable so fallback word count is used
    monkeypatch.setattr(mgr, "_available", False)
    text = "one two three"
    assert mgr.count_tokens(text) == 3


def test_gemini_manager_no_api_key():
    mgr = llm_clients.GeminiClientManager(api_key=None, default_model_name="dummy")
    assert not mgr.available
    resp = mgr.generate_response([])
    assert "not available" in resp 