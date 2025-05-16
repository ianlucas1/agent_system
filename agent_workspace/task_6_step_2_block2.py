# This file contains a scaffold for a task.
# The content below is the raw scaffold:

"""
cost_path = pathlib.Path("agent_workspace/cost_cache.json")
  if cost_path.exists():
      data = json.loads(cost_path.read_text())
      st.sidebar.markdown(f"💵 OpenAI last 24h: ${data.get('openai_24h', 'N/A'):.2f}")
      st.sidebar.markdown(f"💵 Gemini est.: ${data.get('gemini_est', 'N/A'):.2f}")
"""