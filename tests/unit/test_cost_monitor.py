import os
import json
import tempfile
import pathlib
import pytest
from unittest import mock

# Patch the polling interval to a small value for testing
@pytest.fixture(autouse=True)
def patch_ttl(monkeypatch):
    monkeypatch.setattr("src.shared.cost_monitor.TTL", 1)

@mock.patch("src.shared.cost_monitor.requests.get")
def test_cost_monitor_openai_and_gemini(mock_get, monkeypatch):
    # Setup temp dir for agent_workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = pathlib.Path(tmpdir) / "cost_cache.json"
        monkeypatch.setattr("src.shared.cost_monitor.CACHE", cache_path)

        # Patch UsageLogger.get_totals in the correct module
        monkeypatch.setattr(
            "src.shared.usage_logger.UsageLogger.get_totals",
            staticmethod(lambda: {"gemini": 12345, "openai": 0})
        )

        # Patch threading.Thread in cost_monitor to prevent background thread
        monkeypatch.setattr("src.shared.cost_monitor.threading.Thread", lambda *a, **kw: None)

        # Mock OpenAI API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"total_usage": 12345}  # in cents

        # Import and run one poll
        import importlib
        cm = importlib.import_module("src.shared.cost_monitor")
        cm._poll_openai = mock.Mock(wraps=cm._poll_openai)
        # Run _poll once (not the thread)
        def single_poll():
            from src.shared.cost_monitor import _poll
            # Patch time.sleep to break after one loop
            with mock.patch("time.sleep", side_effect=Exception("break")):
                try:
                    _poll()
                except Exception as e:
                    assert str(e) == "break"
        single_poll()

        # Check that the cache file was written and contains expected values
        assert cache_path.exists()
        data = json.loads(cache_path.read_text())
        assert abs(data["openai_24h"] - (12345 / 100.0)) < 1e-6
        assert abs(data["gemini_est"] - (12345 * 0.00003)) < 1e-6 