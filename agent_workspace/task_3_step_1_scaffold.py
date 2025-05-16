# This file contains a scaffold for a task.
# The content below is the raw scaffold:

"""
import json, threading, time, pathlib
  LOG_PATH = pathlib.Path("agent_workspace/usage_log.json")
  FLUSH_SEC = 60

  class UsageLogger:
      _totals = {"openai": 0, "gemini": 0}
      _accum  = {"openai": 0, "gemini": 0}

      @classmethod
      def inc(cls, provider: str, n: int):
          cls._accum[provider] += n
          cls._totals[provider] += n

      @classmethod
      def get_totals(cls) -> dict:
          return cls._totals.copy()

      @classmethod
      def _flush(cls):
          data = {"timestamp": int(time.time())} | cls._accum
          LOG_PATH.parent.mkdir(exist_ok=True)
          with LOG_PATH.open("a") as f:
              f.write(json.dumps(data) + '\n')
          cls._accum = {"openai": 0, "gemini": 0}

  def _loop():
      while True:
          time.sleep(FLUSH_SEC)
          UsageLogger._flush()

  threading.Thread(target=_loop, daemon=True).start()
"""