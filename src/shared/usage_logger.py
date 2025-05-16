import json
import threading
import time
import pathlib

from src.shared.metrics import MetricsManager

# Path to log file inside the agent_workspace directory
LOG_PATH = pathlib.Path("agent_workspace/usage_log.json")
# How often to flush the in-memory counters to disk (seconds)
FLUSH_SEC = 60


class UsageLogger:
    """Simple process-level token accounting + periodic persistence.

    The class keeps two dicts in memory:
        _accum  – tokens since the last flush (written to disk at FLUSH_SEC cadence)
        _totals – lifetime counts for the current process (since import)

    The static design keeps things extremely lightweight and avoids the need for
    explicit instantiation across modules.
    """

    _totals: dict[str, int] = {"openai": 0, "gemini": 0}
    _accum: dict[str, int] = {"openai": 0, "gemini": 0}

    @classmethod
    def inc(cls, provider: str, n: int) -> None:
        """Increment the counters for *provider* by *n* tokens.

        If Prometheus metrics are enabled (see MetricsManager) we increment the
        respective counter there as well so the values are observable at
        /metrics.
        """
        if n <= 0:
            return  # Ignore non-positive counts to avoid negative drift
        if provider not in cls._totals:
            # Lazily add unknown providers to avoid hard failures.
            cls._totals[provider] = 0
            cls._accum[provider] = 0

        cls._accum[provider] += n
        cls._totals[provider] += n

        # Propagate to Prometheus if available / enabled.
        mm = MetricsManager()
        if mm.enabled and hasattr(mm, f"{provider}_tokens_total"):
            getattr(mm, f"{provider}_tokens_total").inc(n)

    @classmethod
    def get_totals(cls) -> dict:
        """Return a shallow copy of the running totals."""
        return cls._totals.copy()

    @classmethod
    def _flush(cls) -> None:
        """Flush the _accum counts to disk and reset the accumulator."""
        # Skip writing empty deltas to avoid noisy logs
        if not any(cls._accum.values()):
            return

        data = {"timestamp": int(time.time())} | cls._accum
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        # Reset accumulator after successful write
        cls._accum = {key: 0 for key in cls._accum}


# ---------------------------------------------------------------------------
# Background flush thread – only started once at import time
# ---------------------------------------------------------------------------

def _loop() -> None:
    while True:
        time.sleep(FLUSH_SEC)
        try:
            UsageLogger._flush()
        except Exception:  # nosec B110 - Intentionally swallowing exceptions to prevent background thread from crashing application.
            # Never let the background thread kill the process – swallow errors
            pass


# Start the background thread as a daemon so it does not block process exit
threading.Thread(target=_loop, daemon=True, name="usage_logger_flush").start() 