import json

import pytest

from src.shared import usage_logger as UL


def test_usage_logger_flush(tmp_path, monkeypatch):
    """Calling UsageLogger.inc followed by manual _flush should write a line to the log file."""
    # Redirect log path to a temporary location to keep workspace clean
    test_log = tmp_path / "usage_log.json"
    monkeypatch.setattr(UL, "LOG_PATH", test_log, raising=False)

    # Ensure accumulator is reset for deterministic counts
    UL.UsageLogger._accum = {"openai": 0, "gemini": 0}
    UL.UsageLogger._totals = {"openai": 0, "gemini": 0}

    UL.UsageLogger.inc("openai", 5)

    # Force a flush without waiting for the background thread
    UL.UsageLogger._flush()

    # Verify line is written
    assert test_log.exists(), "usage_log.json should be created after flush"
    lines = test_log.read_text().strip().splitlines()
    assert len(lines) == 1, "Exactly one log entry expected"

    data = json.loads(lines[-1])
    # Timestamp should be present
    assert "timestamp" in data
    assert data["openai"] == 5
    # Gemini count should be zero by default
    assert data["gemini"] == 0 