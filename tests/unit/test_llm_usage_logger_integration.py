import importlib

from src.llm import clients as llm_clients
from src.shared import usage_logger as UL


def test_openai_client_no_api_key(monkeypatch):
    # Ensure counters start at zero
    UL.UsageLogger._accum = {"openai": 0, "gemini": 0}
    UL.UsageLogger._totals = {"openai": 0, "gemini": 0}

    mgr = llm_clients.OpenAIClientManager(api_key=None, default_model_name="dummy")
    assert mgr.available is False

    resp = mgr.generate_response([])
    assert "not available" in resp.lower()

    # Token count fallback should work without SDK/tiktoken
    tokens = mgr.count_tokens("one two three")
    assert tokens == 3

    # Manually invoke UsageLogger to simulate accounting
    UL.UsageLogger.inc("openai", tokens)

    totals = UL.UsageLogger.get_totals()
    assert totals["openai"] == 3


def test_gemini_client_no_api_key(monkeypatch):
    UL.UsageLogger._accum = {"openai": 0, "gemini": 0}
    UL.UsageLogger._totals = {"openai": 0, "gemini": 0}

    mgr = llm_clients.GeminiClientManager(api_key=None, default_model_name="dummy")
    assert mgr.available is False

    resp = mgr.generate_response([])
    assert "not available" in resp.lower()

    tokens = mgr.count_tokens("alpha beta gamma delta")
    assert tokens == 4
    UL.UsageLogger.inc("gemini", tokens)
    totals = UL.UsageLogger.get_totals()
    assert totals["gemini"] == 4 