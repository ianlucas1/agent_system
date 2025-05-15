import json
import pytest

from src.shared.context_bus import ContextBus, ContextBusFullError


def test_set_and_get(tmp_path):
    ctx_file = tmp_path / "context.json"
    bus = ContextBus(path=ctx_file)
    # Initially should have no value
    assert bus.get("foo") is None
    # Set and get
    bus.set("foo", "bar")
    assert bus.get("foo") == "bar"
    # File should exist and be valid JSON
    content = json.loads(ctx_file.read_text(encoding="utf-8"))
    assert content.get("foo") == "bar"


def test_append(tmp_path):
    ctx_file = tmp_path / "context.json"
    bus = ContextBus(path=ctx_file)
    bus.set("foo", "bar")
    bus.append("foo", "baz")
    expected = "bar\n---\nbaz"
    assert bus.get("foo") == expected
    # Ensure file content reflects appended value
    content = json.loads(ctx_file.read_text(encoding="utf-8"))
    assert content.get("foo") == expected


def test_size_guard(tmp_path):
    ctx_file = tmp_path / "context.json"
    bus = ContextBus(path=ctx_file)
    # Create a big value near the limit
    big_val = "x" * (200 * 1024 - 10)
    bus.set("large", big_val)
    # Appending more should exceed size and raise
    with pytest.raises(ContextBusFullError):
        bus.append("large", "more") 