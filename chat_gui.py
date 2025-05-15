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

# --- Start of new model selection logic ---
openai_models_list = [
    "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
    "gpt-4o-latest", "o4-mini", "o3",
]
gemini_models_list = [
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-flash-preview-04-17",
]

# Create a list of (display_name, model_name, provider) tuples
# For now, display_name and model_name are the same.
all_models_structured = [
    (name, name, "openai") for name in openai_models_list
] + [
    (name, name, "gemini") for name in gemini_models_list
]

model_display_names = [item[0] for item in all_models_structured]

# Determine default index for the unified dropdown
current_selected_model_name = st.session_state.get("selected_model_name", chat_session.openai_model) # Default to openai_model
if current_selected_model_name not in model_display_names:
    # If current is a Gemini model and not in combined list (e.g. from previous structure)
    current_selected_model_name = st.session_state.get("gemini_model_name", chat_session.gemini_model)
    if current_selected_model_name not in model_display_names:
        current_selected_model_name = openai_models_list[0] # Fallback to first OpenAI model

default_idx = 0
if current_selected_model_name in model_display_names:
    default_idx = model_display_names.index(current_selected_model_name)

chosen_display_model = st.sidebar.selectbox(
    "Choose Model",
    model_display_names,
    index=default_idx,
    key="selected_model_name" # Store the chosen display name
)

# Find the chosen model details (name and provider)
selected_model_name = chosen_display_model
selected_provider = "openai" # Default provider
for _, name, provider_val in all_models_structured:
    if name == chosen_display_model:
        selected_provider = provider_val
        break

# Update chat_session with the specific model and globally set provider for process_user_message
st.session_state.active_provider = selected_provider
if selected_provider == "openai":
    chat_session.openai_model = selected_model_name
    # Ensure gemini_model on chat_session is also a valid default if user switches provider later
    if not hasattr(chat_session, 'gemini_model') or chat_session.gemini_model not in gemini_models_list:
        chat_session.gemini_model = gemini_models_list[0]
elif selected_provider == "gemini":
    chat_session.gemini_model = selected_model_name
    # Ensure openai_model on chat_session is also a valid default
    if not hasattr(chat_session, 'openai_model') or chat_session.openai_model not in openai_models_list:
        chat_session.openai_model = openai_models_list[0]

# --- End of new model selection logic ---

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
            chat_session.process_user_message(user_message, model_choice=st.session_state.active_provider, specific_model_name=selected_model_name)
        st.rerun()
