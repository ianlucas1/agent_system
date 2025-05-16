# This file contains a scaffold for a task.
# The content below is the raw scaffold:

"""
import shared.usage_logger as UL
  with st.sidebar.expander("Token & Cost Stats", expanded=True):
      totals = UL.UsageLogger.get_totals()
      st.markdown(f"**OpenAI:** {totals['openai']:,} tok")
      st.markdown(f"**Gemini:** {totals['gemini']:,} tok")
"""