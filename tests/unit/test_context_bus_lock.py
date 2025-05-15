import threading
import json
import pytest
# from pathlib import Path (unused)

from src.shared.context_bus import ContextBus, ContextBusLockTimeout


def test_concurrent_writes(tmp_path):
    ctx_file = tmp_path / "context.json"
    # Two buses pointing to same file
    bus1 = ContextBus(path=ctx_file)
    bus2 = ContextBus(path=ctx_file)

    def worker(bus, val):
        bus.set("key", val)

    t1 = threading.Thread(target=worker, args=(bus1, "A"))
    t2 = threading.Thread(target=worker, args=(bus2, "B"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Final value should be one of the last writes
    content = json.loads(ctx_file.read_text(encoding="utf-8"))
    assert content.get("key") in ("A", "B")


def test_lock_timeout(tmp_path, monkeypatch):
    ctx_file = tmp_path / "context.json"
    bus = ContextBus(path=ctx_file)
    # Override file_lock in context_bus to always timeout
    import src.shared.context_bus as cb
    monkeypatch.setattr(cb, 'file_lock', lambda *args, **kwargs: (_ for _ in ()).throw(cb.ContextBusLockTimeout("timeout")))
    with pytest.raises(ContextBusLockTimeout):
        bus.set("foo", "bar") 