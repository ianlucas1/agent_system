"""
chat_gui.py - Streamlit web application for the chat interface.
Provides a UI for chatting with OpenAI and Gemini models, and using file system commands.
"""
import streamlit as st
from chat_session import ChatSession
import os

# Page configuration
st.set_page_config(page_title="Chat with Agent System", page_icon="💬", layout="centered")

# Initialize chat session in session_state if not already
if "chat_session" not in st.session_state:
    st.session_state.chat_session = ChatSession()
chat_session = st.session_state.chat_session

# Sidebar - API status and controls
st.sidebar.header("Model Selection & Settings")
# Top-level model choice (provider)
model_display = st.sidebar.selectbox(
    "Choose Model Provider",
    ["OpenAI", "Gemini", "Both (OpenAI + Gemini)"],
    index=0 if "selected_model" not in st.session_state else {"openai": 0, "gemini": 1, "both": 2}[st.session_state.selected_model],
)

# Available model variants
openai_models = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4o-2024-05-13",
    "gpt-4-turbo",
    "gpt-3.5-turbo-0125",
]

gemini_models = [
    "gemini-2.5-pro-preview-05-06",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

# Model variant selection
if model_display in ("openai", "both"):
    default_idx = openai_models.index(st.session_state.get("openai_model", chat_session.openai_model)) if st.session_state.get("openai_model", chat_session.openai_model) in openai_models else 0
    openai_choice = st.sidebar.selectbox("OpenAI model", openai_models, index=default_idx, key="openai_model")
    chat_session.openai_model = openai_choice

if model_display in ("gemini", "both"):
    default_g_idx = gemini_models.index(st.session_state.get("gemini_model", chat_session.gemini_model)) if st.session_state.get("gemini_model", chat_session.gemini_model) in gemini_models else 0
    gemini_choice = st.sidebar.selectbox("Gemini model", gemini_models, index=default_g_idx, key="gemini_model")
    chat_session.gemini_model = gemini_choice

st.session_state.selected_model = model_display

# Collaborative mode checkbox (only when both models selected)
use_a2a = False
if model_display == "both":
    use_a2a = st.sidebar.checkbox("Enable collaboration (A2A)", value=st.session_state.get("use_a2a", False),
                                  key="use_a2a")
else:
    st.session_state.use_a2a = False

# Display API key status
openai_status = "✅ Connected" if chat_session.openai_available else (
    "❌ (no API key)" if os.getenv("OPENAI_API_KEY") in (None, "", "") else "❌ (unavailable)")
gemini_status = "✅ Connected" if chat_session.gemini_available else (
    "❌ (no API key)" if os.getenv("GOOGLE_API_KEY") in (None, "", "") else "❌ (unavailable)")
st.sidebar.markdown(f"**OpenAI**: {openai_status}")
st.sidebar.markdown(f"**Gemini**: {gemini_status}")

# Clear chat button
if st.sidebar.button("Clear Chat"):
    st.session_state.chat_session = ChatSession()
    chat_session = st.session_state.chat_session
    # (Retain model selection in session_state)

st.title("🤖 AI Chat Interface")
# Display chat history
for sender, content in chat_session.chat_log:
    if sender == "user":
        if any(tok in content for tok in ["\n", "```", "- "]):
            st.markdown(f"**You:**\n{content}")
        else:
            st.markdown(f"**You:** {content}")
    elif sender == "openai":
        st.markdown(f"**Agent (OpenAI):**\n{content}")
    elif sender == "gemini":
        st.markdown(f"**Agent (Gemini):**\n{content}")
    elif sender == "collab":
        st.markdown(f"**Agent (OpenAI & Gemini):**\n{content}")

# Overwrite confirmation button if needed
if chat_session.pending_write_path:
    file_name = os.path.basename(chat_session.pending_write_path)
    if st.button(f"Overwrite {file_name}"):
        chat_session.confirm_overwrite()
        st.rerun()

# Input form for new user message
st.write("----")
with st.form(key="chat_form", clear_on_submit=True):
    user_message = st.text_area("Your message:", "", placeholder="Type a message and press send...",
                                label_visibility="collapsed")
    submitted = st.form_submit_button("Send")
    if submitted and user_message.strip():
        with st.spinner("Waiting for response..."):
            chat_session.process_user_message(user_message, model_choice=model_display,
                                              use_a2a=st.session_state.get("use_a2a", False))
        st.rerun()
