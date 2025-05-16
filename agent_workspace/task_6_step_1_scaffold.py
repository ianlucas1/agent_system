# This file contains a scaffold for a task.
# The content below is the raw scaffold:

"""
import os, time, json, pathlib, threading, requests
  CACHE = pathlib.Path("agent_workspace/cost_cache.json")
  TTL   = 900  # 15 minutes

  def _poll_openai():
      key = os.getenv("OPENAI_API_KEY")
      if not key: return None
      try:
          url = "https://api.openai.com/v1/dashboard/billing/usage"
          since = int(time.time() - 86400)
          res = requests.get(f"{url}?start_time={since}&end_time={int(time.time())}",
                              headers={"Authorization": f"Bearer {key}"}, timeout=5)
          res.raise_for_status()
          data = res.json()
          return data.get("total_usage", 0) / 100.0  # cents to dollars
      except Exception:
          return None

  def _poll():
      from shared.usage_logger import UsageLogger
      while True:
          snapshot = {"ts": int(time.time())}
          snapshot["openai_24h"] = _poll_openai()
          # Estimate Gemini cost via token count (if no direct API):
          gem_tokens = UsageLogger.get_totals().get("gemini", 0)
          snapshot["gemini_est"] = gem_tokens * 0.00003  # $0.00003 per token approx
          CACHE.parent.mkdir(exist_ok=True)
          CACHE.write_text(json.dumps(snapshot))
          time.sleep(TTL)

  threading.Thread(target=_poll, daemon=True).start()
"""