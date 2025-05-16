"""
chat_gui.py - Streamlit web application for the chat interface.
Provides a UI for chatting with OpenAI and Gemini models, and using file system commands.
"""

import streamlit as st
from src.core.chat_session import ChatSession
import os
import shared.history as history # Added for persistent history loading and clearing
import shared.usage_logger as UL
import shared.cost_monitor  # Import cost monitor module

# import tiktoken # No longer needed here directly
# import google.generativeai as genai # No longer needed here directly
from src import config  # Updated import
import logging
from typing import Tuple  # For type hints

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Chat Interface", page_icon="��", layout="wide"
)

# Initialize chat session in session_state if not already
if "chat_session" not in st.session_state:
    st.session_state.chat_session = ChatSession()
    # Token counting states
    st.session_state.last_user_input_token_count = 0
    st.session_state.last_user_input_provider = "openai"  # Default, will be updated
    st.session_state.current_user_message_tokens_log = []  # List of (count, provider_str, model_name_str)
    logger.info("New ChatSession initialized for Streamlit session.")  # Added log

    st.session_state.current_conversation_openai_tokens = 0
    st.session_state.current_conversation_gemini_tokens = 0
    st.session_state.all_time_total_openai_tokens = 0
    st.session_state.all_time_total_gemini_tokens = 0

# Load persistent history on app startup
st.session_state.setdefault("messages", history.load())

chat_session = st.session_state.chat_session

# Start cost polling thread on app startup
shared.cost_monitor.start_polling()

# --- Helper Functions for UI Rendering ---


def _render_model_selection_sidebar(chat_session: ChatSession) -> Tuple[str, str]:
    """Renders the model selection dropdown and related logic in the sidebar.
    Returns the selected_model_name and selected_provider.
    """
    st.sidebar.header("Model Selection & Settings")

    openai_models_list = config.AVAILABLE_OPENAI_MODELS
    gemini_models_list = config.AVAILABLE_GEMINI_MODELS

    all_models_structured = (
        [(name, name, "openai") for name in openai_models_list]
        + [(name, name, "gemini") for name in gemini_models_list]
        + [
            (
                "OpenAI & Gemini (Collab)",
                "a2a_collab_v1",
                "collab",
            )  # Added collab option
        ]
    )
    model_display_names = [
        item[0] for item in all_models_structured if item[0]
    ]  # Filter out empty names

    initial_default_model_name = ""  # Default to empty if no models
    if model_display_names:  # Ensure there are models to choose from
        # Try to get a sensible default based on current chat session or config
        if (
            chat_session.openai_manager.available
            and chat_session.openai_model in model_display_names
        ):
            initial_default_model_name = chat_session.openai_model
        elif (
            chat_session.gemini_manager.available
            and chat_session.gemini_model in model_display_names
        ):
            initial_default_model_name = chat_session.gemini_model
        elif config.DEFAULT_OPENAI_MODEL in model_display_names:
            initial_default_model_name = config.DEFAULT_OPENAI_MODEL
        elif config.DEFAULT_GEMINI_MODEL in model_display_names:
            initial_default_model_name = config.DEFAULT_GEMINI_MODEL
        else:
            initial_default_model_name = model_display_names[0]

    current_selected_model_name = st.session_state.get(
        "selected_model_name", initial_default_model_name
    )

    if not model_display_names:
        current_selected_model_name = ""
        default_idx = 0
    elif current_selected_model_name not in model_display_names:
        if (
            initial_default_model_name
            and initial_default_model_name in model_display_names
        ):
            current_selected_model_name = initial_default_model_name
        elif config.DEFAULT_OPENAI_MODEL in model_display_names:
            current_selected_model_name = config.DEFAULT_OPENAI_MODEL
        elif config.DEFAULT_GEMINI_MODEL in model_display_names:
            current_selected_model_name = config.DEFAULT_GEMINI_MODEL
        elif model_display_names:  # Fallback only if list is not empty
            current_selected_model_name = model_display_names[0]
        else:
            current_selected_model_name = ""

    default_idx = 0
    if current_selected_model_name and model_display_names:
        try:
            default_idx = model_display_names.index(current_selected_model_name)
        except ValueError:
            default_idx = 0
    elif model_display_names:
        current_selected_model_name = model_display_names[0]
        default_idx = 0

    if not model_display_names:  # If list is empty, no selectbox
        st.sidebar.warning("No models available for selection. Check config.py.")
        return "", ""

    chosen_display_model = st.sidebar.selectbox(
        "Choose Model",
        options=model_display_names,  # Use options parameter
        index=default_idx,
        key="selected_model_name",
    )

    old_selected_model_in_session = st.session_state.get(
        "selected_model_name_in_session_state_before_selectbox", None
    )
    old_active_provider_in_session = st.session_state.get("active_provider", None)

    newly_selected_provider = "openai"
    for _, name, provider_val in all_models_structured:
        if name == chosen_display_model:
            newly_selected_provider = provider_val
            break

    if (
        old_selected_model_in_session != chosen_display_model
        or old_active_provider_in_session != newly_selected_provider
    ):
        logger.info(
            f"Model selection changed. New model: {chosen_display_model}, New provider: {newly_selected_provider}. Previous model in session: {old_selected_model_in_session}, Previous provider: {old_active_provider_in_session}"
        )

    st.session_state.selected_model_name_in_session_state_before_selectbox = (
        chosen_display_model
    )

    # Update chat_session with the specific model and globally set provider for process_user_message
    st.session_state.active_provider = newly_selected_provider
    if newly_selected_provider == "openai":
        chat_session.openai_model = chosen_display_model
        if (
            not hasattr(chat_session, "gemini_model")
            or chat_session.gemini_model not in gemini_models_list
        ):
            if gemini_models_list:
                chat_session.gemini_model = (
                    config.DEFAULT_GEMINI_MODEL
                    if config.DEFAULT_GEMINI_MODEL in gemini_models_list
                    else gemini_models_list[0]
                )
    elif newly_selected_provider == "gemini":
        chat_session.gemini_model = chosen_display_model
        if (
            not hasattr(chat_session, "openai_model")
            or chat_session.openai_model not in openai_models_list
        ):
            if openai_models_list:
                chat_session.openai_model = (
                    config.DEFAULT_OPENAI_MODEL
                    if config.DEFAULT_OPENAI_MODEL in openai_models_list
                    else openai_models_list[0]
                )
    elif newly_selected_provider == "collab":
        # For collab, we don't set a single model on chat_session in the same way
        # ChatSession.process_user_message will handle model_choice="collab"
        # Ensure both managers have a valid default model selected internally from config for when collab is called.
        # This is already handled by ChatSession.__init__ setting defaults on managers.
        logger.info(
            f"Collaboration mode selected. Specific model for OpenAI part of collab: {chat_session.openai_model}, for Gemini part: {chat_session.gemini_model}"
        )
        pass  # No specific single model to set on chat_session for 'collab' mode here

    return chosen_display_model, newly_selected_provider


def _render_api_status_sidebar(chat_session: ChatSession):
    """Renders the API connection status in the sidebar."""
    openai_status = (
        "✅ Connected"
        if chat_session.openai_available
        else ("❌ (no API key)" if not config.OPENAI_API_KEY else "❌ (unavailable)")
    )
    gemini_status = (
        "✅ Connected"
        if chat_session.gemini_available
        else ("❌ (no API key)" if not config.GOOGLE_API_KEY else "❌ (unavailable)")
    )
    st.sidebar.markdown(f"**OpenAI**: {openai_status}")
    st.sidebar.markdown(f"**Gemini**: {gemini_status}")


def _update_and_display_token_counts(chat_session: ChatSession):
    """Calculates current conversation tokens and updates sidebar display."""
    user_openai_tokens = 0
    user_gemini_tokens = 0
    if "current_user_message_tokens_log" in st.session_state:
        for (
            count,
            provider,
            _model_name,
        ) in st.session_state.current_user_message_tokens_log:
            if provider == "openai":
                user_openai_tokens += count
            elif provider == "gemini":
                user_gemini_tokens += count

    agent_openai_tokens = 0
    agent_gemini_tokens = 0
    for sender, content in chat_session.chat_log:
        if sender == "openai":
            if chat_session.openai_manager and chat_session.openai_manager.available:
                agent_openai_tokens += chat_session.openai_manager.count_tokens(content)
            else:
                agent_openai_tokens += len(content.split())
        elif sender == "gemini":
            if chat_session.gemini_manager and chat_session.gemini_manager.available:
                agent_gemini_tokens += chat_session.gemini_manager.count_tokens(content)
            else:
                agent_gemini_tokens += len(content.split())

    st.session_state.current_conversation_openai_tokens = (
        user_openai_tokens + agent_openai_tokens
    )
    st.session_state.current_conversation_gemini_tokens = (
        user_gemini_tokens + agent_gemini_tokens
    )


def _render_token_counts_sidebar():
    """Renders the token count display in the sidebar."""
    if (
        "chat_session" in st.session_state
    ):  # Ensure counts are calculated if session exists
        _update_and_display_token_counts(st.session_state.chat_session)

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### Token Counts")
    last_provider_display = st.session_state.get("last_user_input_provider", "N/A")
    st.sidebar.markdown(
        f"**Last Input:** {st.session_state.get('last_user_input_token_count', 0)} tokens ({last_provider_display})"
    )
    current_openai = st.session_state.get("current_conversation_openai_tokens", 0)
    current_gemini = st.session_state.get("current_conversation_gemini_tokens", 0)
    st.sidebar.markdown("**Current Chat:**")
    st.sidebar.markdown(f"&nbsp;&nbsp;OpenAI: {current_openai}")
    st.sidebar.markdown(f"&nbsp;&nbsp;Gemini: {current_gemini}")
    st.sidebar.markdown(f"&nbsp;&nbsp;Total: {current_openai + current_gemini}")
    all_time_openai = st.session_state.get("all_time_total_openai_tokens", 0)
    all_time_gemini = st.session_state.get("all_time_total_gemini_tokens", 0)
    st.sidebar.markdown("**All Time:**")
    st.sidebar.markdown(f"&nbsp;&nbsp;OpenAI: {all_time_openai}")
    st.sidebar.markdown(f"&nbsp;&nbsp;Gemini: {all_time_gemini}")
    st.sidebar.markdown(f"&nbsp;&nbsp;Total: {all_time_openai + all_time_gemini}")
    st.sidebar.markdown("---")

    # --- Cost Monitor Panel ---
    import pathlib
    import json
    cost_path = pathlib.Path("agent_workspace/cost_cache.json")
    if cost_path.exists():
        data = json.loads(cost_path.read_text())
        st.sidebar.markdown(f"💵 OpenAI last 24h: ${data.get('openai_24h', 'N/A'):.2f}")
        st.sidebar.markdown(f"💵 Gemini est.: ${data.get('gemini_est', 'N/A'):.2f}")


def _render_clear_chat_button() -> bool:
    """Renders the Clear Chat button in the sidebar."""
    if st.sidebar.button("🗑 Clear Chat"):
        history.reset()
        st.session_state["messages"] = []
        st.rerun()
        return True
    return False


def _render_chat_history(chat_session: ChatSession):
    """Renders the chat message history in the main area."""
    for sender, content in chat_session.chat_log:
        if sender == "user":
            if any(tok in content for tok in ["\\n", "```", "- "]):
                st.markdown(f"**You:**\\n{content}")
            else:
                st.markdown(f"**You:** {content}")
        elif sender == "openai":
            st.markdown(f"**Agent (OpenAI):**\\n{content}")
        elif sender == "gemini":
            st.markdown(f"**Agent (Gemini):**\\n{content}")
        elif sender == "collab":
            st.markdown(f"**Agent (OpenAI & Gemini):**\\n{content}")
        # else:
        #     st.markdown(f"**{sender.capitalize()}:**\\n{content}") # Generic sender


def _render_overwrite_confirmation(chat_session: ChatSession) -> bool:
    """Renders the overwrite confirmation button if a pending write exists. Returns True if confirmed."""
    if chat_session.pending_write_user_path:
        file_name = os.path.basename(chat_session.pending_write_user_path)
        if st.button(f"Overwrite {file_name}"):
            chat_session.confirm_overwrite()
            return True
    return False


def _render_input_form(
    chat_session: ChatSession,
    selected_model_name_from_sidebar: str,
    selected_provider_from_sidebar: str,
):
    """Renders the user input form and handles message submission."""
    st.write("----")
    with st.form(key="chat_form", clear_on_submit=True):
        user_message = st.text_area(
            "Your message:",
            "",
            placeholder="Type a message and press send...",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send")
        if submitted and user_message.strip():
            with st.spinner("Waiting for response..."):
                active_provider = (
                    st.session_state.active_provider
                )  # This should be the one set by model selector

                logger.debug(
                    f"Form submitted. Active provider: {active_provider}, Model for processing: {selected_model_name_from_sidebar}, User message: '{user_message[:50]}...'"
                )

                current_input_tokens = 0
                if active_provider == "openai":
                    if (
                        chat_session.openai_manager
                        and chat_session.openai_manager.available
                    ):
                        current_input_tokens = chat_session.openai_manager.count_tokens(
                            user_message
                        )
                    else:
                        current_input_tokens = len(user_message.split())
                elif active_provider == "gemini":
                    if (
                        chat_session.gemini_manager
                        and chat_session.gemini_manager.available
                    ):
                        current_input_tokens = chat_session.gemini_manager.count_tokens(
                            user_message
                        )
                    else:
                        current_input_tokens = len(user_message.split())

                st.session_state.last_user_input_token_count = current_input_tokens
                st.session_state.last_user_input_provider = active_provider
                st.session_state.current_user_message_tokens_log.append(
                    (
                        current_input_tokens,
                        active_provider,
                        selected_model_name_from_sidebar,
                    )
                )

                chat_session.process_user_message(
                    user_message,
                    model_choice=active_provider,
                    specific_model_name=selected_model_name_from_sidebar,
                )
                logger.debug(
                    "Finished processing user message, preparing to update token counts and rerun."
                )
            return True  # Indicates a message was submitted and processed
    return False


# --- Main Application ---
def main_gui():
    logger.info("Streamlit GUI application started/reloaded.")

    # Initialize chat session in session_state if not already present
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = ChatSession()
        st.session_state.last_user_input_token_count = 0
        st.session_state.last_user_input_provider = "openai"
        st.session_state.current_user_message_tokens_log = []
        st.session_state.current_conversation_openai_tokens = 0
        st.session_state.current_conversation_gemini_tokens = 0
        st.session_state.all_time_total_openai_tokens = 0
        st.session_state.all_time_total_gemini_tokens = 0
        logger.info(
            "New ChatSession and token states initialized for Streamlit session."
        )

    chat_session_instance = st.session_state.chat_session

    # Sidebar rendering
    selected_model, active_provider = _render_model_selection_sidebar(
        chat_session_instance
    )
    # --- Task 5: Token & Cost Stats Expander ---
    with st.sidebar.expander("Token & Cost Stats", expanded=True):
        totals = UL.UsageLogger.get_totals()
        st.markdown(f"**OpenAI:** {totals['openai']:,} tok")
        st.markdown(f"**Gemini:** {totals['gemini']:,} tok")
    # --- End Task 5 addition ---
    _render_api_status_sidebar(chat_session_instance)
    _render_token_counts_sidebar()  # This will call _update_and_display_token_counts inside

    if _render_clear_chat_button():
        st.rerun()  # Rerun if chat was cleared

    # Main area rendering
    st.title("🤖 AI Chat Interface")
    _render_chat_history(chat_session_instance)

    if _render_overwrite_confirmation(chat_session_instance):
        st.rerun()  # Rerun if overwrite was confirmed

    if _render_input_form(chat_session_instance, selected_model, active_provider):
        # _update_and_display_token_counts is implicitly called by _render_token_counts_sidebar on rerun,
        # or explicitly if needed after processing.
        # For now, the rerun after form submission will trigger _render_token_counts_sidebar.
        _update_and_display_token_counts(
            chat_session_instance
        )  # Explicit call after processing
        st.rerun()

    # Add copy-to-clipboard JS for code blocks
    st.markdown(
        """
        <script>
        function addCopyButtons() {
            document.querySelectorAll('pre code').forEach(function(codeBlock) {
                if (codeBlock.parentElement.querySelector('.copy-btn')) return;
                var button = document.createElement('button');
                button.className = 'copy-btn';
                button.textContent = 'Copy';
                button.style = 'float: right; margin: 4px; padding: 2px 8px; font-size: 0.8em;';
                button.onclick = function() {
                    navigator.clipboard.writeText(codeBlock.innerText);
                    button.textContent = 'Copied!';
                    setTimeout(function() { button.textContent = 'Copy'; }, 1200);
                };
                codeBlock.parentElement.insertBefore(button, codeBlock);
            });
        }
        setTimeout(addCopyButtons, 500);
        document.addEventListener('DOMNodeInserted', addCopyButtons);
        </script>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main_gui()
