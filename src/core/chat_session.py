"""
chat_session.py - Defines the ChatSession class for managing multi-turn conversations,
command parsing, and routing to language models and file operations.
"""

from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

from src import config  # Updated import
import logging

# Import the file manager module for file operations
# (file_manager itself is used by tools.FileManagerTool, not directly by ChatSession anymore)
# try:
#     from . import file_manager
# except ImportError:
#     import file_manager

from src.handlers.command import CommandHandler, Command  # Updated import
from src.llm.clients import OpenAIClientManager, GeminiClientManager  # Updated import
from src.tools.file_system import FileManagerTool  # Updated import
from src.tools.base import ToolInput  # Updated import
import shared.history as history  # Added for persistent history

logger = logging.getLogger(__name__)  # Added


# --- Start of new History Management Classes ---
@dataclass
class Message:
    role: str  # "system", "user", or "assistant"
    content: str
    # sender_provider helps distinguish who generated an "assistant" message for chat_log display
    # or to identify the user or system easily.
    sender_provider: Optional[str] = (
        None  # e.g., "user", "system", "openai", "gemini", "collab"
    )


class ConversationHistory:
    def __init__(self, system_prompt_content: str):
        self.messages: List[Message] = []
        if system_prompt_content:
            logger.debug(
                "Initializing ConversationHistory with system prompt."
            )  # Added log
            self.add_message(
                role="system", content=system_prompt_content, sender_provider="system"
            )

    def add_message(self, role: str, content: str, sender_provider: Optional[str]):
        logger.debug(
            f"Adding message to history: Role={role}, Provider={sender_provider}, Content='{content[:50]}...' "
        )  # Added log
        self.messages.append(
            Message(role=role, content=content, sender_provider=sender_provider)
        )

    def clear_chat(self, system_prompt_content: str):
        logger.info("Clearing chat history.")  # Added log
        self.messages = []
        if system_prompt_content:
            self.add_message(
                role="system", content=system_prompt_content, sender_provider="system"
            )

    def get_chat_log(self) -> List[Tuple[str, str]]:
        """Formats history for display (compatible with old chat_log format)."""
        display_log = []
        for msg in self.messages:
            if msg.role == "user":
                display_log.append(("user", msg.content))
            elif msg.role == "assistant":
                # msg.sender_provider should be "openai" or "gemini" for assistant messages
                # or potentially "collab" in the future.
                # Default to "assistant" if sender_provider is None for some reason, though it shouldn't be.
                sender = msg.sender_provider if msg.sender_provider else "assistant"
                display_log.append((sender, msg.content))
            # System messages are generally not included in the display chat_log
        return display_log

    def get_openai_format(self) -> List[Dict[str, str]]:
        """Formats history for OpenAI API (roles: system, user, assistant)."""
        formatted_messages = []
        for msg in self.messages:
            # OpenAI expects roles "system", "user", or "assistant".
            # Our Message.role should align with this.
            if msg.role in ["system", "user", "assistant"]:
                formatted_messages.append({"role": msg.role, "content": msg.content})
        return formatted_messages

    def get_gemini_format(self) -> List[Dict[str, str]]:
        """
        Formats history for Gemini API (which also takes a list of dicts for its chat mode,
        similar to OpenAI, before the manager formats it further into a string if needed).
        """
        # Gemini typically uses "user" and "model" roles in its newer chat APIs.
        # However, our GeminiClientManager._format_history_for_gemini currently expects
        # "system", "user", "assistant" and converts "system" specially.
        # So, we provide the same format as for OpenAI for now.
        # If GeminiClientManager is updated to use glm.Content parts, this might change.
        gemini_messages = []
        for msg in self.messages:
            if msg.role == "system":
                # Gemini manager handles system prompt by prepending it.
                # So pass it along.
                gemini_messages.append({"role": "system", "content": msg.content})
            elif msg.role == "user":
                gemini_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                gemini_messages.append({"role": "assistant", "content": msg.content})
        return gemini_messages


# --- End of new History Management Classes ---


class ChatSession:
    """
    ChatSession manages a conversation with one or two LLMs, including message history,
    command parsing (/read, /write, /list, /overwrite), and integration with file system and optional A2A collaboration.
    """

    def __init__(self):
        # Initialize API clients and state
        # load_dotenv() # Removed, now done in config.py

        # Get API keys and default model names from config module
        openai_api_key = config.OPENAI_API_KEY
        google_api_key = config.GOOGLE_API_KEY
        default_openai_model = config.DEFAULT_OPENAI_MODEL
        default_gemini_model = config.DEFAULT_GEMINI_MODEL

        # Initialize LLM client managers
        self.openai_manager = OpenAIClientManager(
            api_key=openai_api_key, default_model_name=default_openai_model
        )
        self.gemini_manager = GeminiClientManager(
            api_key=google_api_key, default_model_name=default_gemini_model
        )

        self.file_tool = FileManagerTool()
        self.command_handler = CommandHandler(
            file_tool=self.file_tool
        )  # Changed and initialized with file_tool

        # Initialize ConversationHistory
        # System prompt could also come from config.py if desired: config.DEFAULT_SYSTEM_PROMPT
        self.system_prompt = (
            "You are a helpful AI assistant. You have access to a local project file system. "
            "You can read files, write files (with user confirmation), and list directories when asked."
        )
        self.history = ConversationHistory(system_prompt_content=self.system_prompt)

        # Pending write operation data (for overwrite confirmation)
        self.pending_write_user_path: Optional[str] = None
        self.pending_write_content: Optional[str] = None
        # Track last model used for context synchronization
        self.last_model = None

    @property
    def openai_available(self) -> bool:
        return self.openai_manager.available

    @property
    def gemini_available(self) -> bool:
        return self.gemini_manager.available

    @property
    def openai_model(self) -> str:
        return self.openai_manager.get_model_name()

    @openai_model.setter
    def openai_model(self, model_name: str):
        self.openai_manager.set_model_name(model_name)

    @property
    def gemini_model(self) -> str:
        return self.gemini_manager.get_model_name()

    @gemini_model.setter
    def gemini_model(self, model_name: str):
        self.gemini_manager.set_model_name(model_name)

    @property
    def chat_log(self) -> List[Tuple[str, str]]:
        return self.history.get_chat_log()

    def process_user_message(
        self,
        user_input: str,
        model_choice: str = "openai",
        specific_model_name: Optional[str] = None,
        use_a2a: bool = False,
    ):
        """
        Process a user input message, handle commands or get response from model(s).
        model_choice: "openai" or "gemini" (acts as provider based on GUI selection).
        specific_model_name: The exact model name selected in the GUI (e.g., "gpt-4.1", "gemini-2.5-pro-preview-05-06")
        use_a2a: Currently unused due to single model selection GUI.
        Returns a list of (sender, content) tuples representing the assistant responses generated.
        """
        processed_user_input = (
            user_input.strip()
        )  # Renamed to avoid conflict with original user_input

        # Update the relevant model in the session if a specific one is passed
        if specific_model_name:
            if model_choice == "openai":
                self.openai_manager.set_model_name(specific_model_name)
                logger.info(f"OpenAI model changed to: {specific_model_name}")
            elif model_choice == "gemini":
                success = self.gemini_manager.set_model_name(specific_model_name)
                if success:
                    logger.info(f"Gemini model changed to: {specific_model_name}")
                else:
                    logger.warning(
                        f"Attempt to change Gemini model to {specific_model_name} encountered issues (see previous logs from GeminiClientManager)."
                    )

        self.last_model = model_choice
        logger.debug(
            f"Processing user message. Model choice: {model_choice}, Last model: {self.last_model}, User input: '{processed_user_input[:50]}...' "
        )  # Added log

        self.history.add_message(
            role="user", content=processed_user_input, sender_provider="user"
        )
        history.append("user", processed_user_input) # Append user message to persistent history

        # Check and handle file system commands using the new CommandHandler
        output_messages = []

        parsed_command: Optional[Command] = self.command_handler.parse(
            processed_user_input, self.history.get_chat_log()
        )

        if parsed_command:
            logger.info(
                f"Parsed command: {parsed_command.command_type} with args: {parsed_command.args}"
            )  # Added log
            command_response_text = self.command_handler.execute_command(
                parsed_command, self, processed_user_input
            )

            if command_response_text:
                logger.info(
                    f"Command response generated: '{command_response_text[:100]}...' "
                )  # Added log
                # Command output is treated as an assistant message
                output_messages.append((model_choice, command_response_text))

        # If no command was parsed, get model response
        if not parsed_command:
            if model_choice == "openai":
                if not self.openai_manager.available:
                    error_msg = "⚠️ OpenAI model is not available."
                    logger.warning("OpenAI model unavailable for user message processing.")
                    self.history.add_message(
                        role="assistant", content=error_msg, sender_provider="openai"
                    )
                    output_messages.append(("openai", error_msg))
                    return output_messages

                logger.debug(
                    f"Sending request to OpenAI model: {self.openai_manager.get_model_name()}"
                )
                answer = self.openai_manager.generate_response(
                    self.history.get_openai_format()
                )
                logger.debug(f"Received answer from OpenAI: '{answer[:100]}...' ")
                self.history.add_message(
                    role="assistant", content=answer, sender_provider="openai"
                )
                output_messages.append(("openai", answer))

            elif model_choice == "gemini":
                if not self.gemini_manager.available:
                    error_msg = "⚠️ Gemini model is not available."
                    logger.warning("Gemini model unavailable for user message processing.")
                    self.history.add_message(
                        role="assistant", content=error_msg, sender_provider="gemini"
                    )
                    output_messages.append(("gemini", error_msg))
                    return output_messages

                logger.debug(
                    f"Sending request to Gemini model: {self.gemini_manager.get_model_name()}"
                )
                answer = self.gemini_manager.generate_response(
                    self.history.get_gemini_format()
                )
                logger.debug(f"Received answer from Gemini: '{answer[:100]}...' ")
                self.history.add_message(
                    role="assistant", content=answer, sender_provider="gemini"
                )
                output_messages.append(("gemini", answer))

        # Add model responses to conversation history and collect for display
        for sender, content in output_messages:
            # Determine the role based on sender for history storage (typically 'assistant' for LLMs)
            role = "assistant"
            # Use sender_provider to store the actual source ('openai', 'gemini', 'collab')
            sender_provider = sender # Use sender directly as it indicates openai/gemini/collab

            self.history.add_message(role=role, content=content, sender_provider=sender_provider)
            history.append(sender_provider, content) # Append agent message to persistent history

        # Check if the last message was a file write command response that requires confirmation
        if parsed_command and parsed_command.command_type == "write" and not parsed_command.args.get("overwrite", False):
            # Assuming args contains 'path' and 'content' for write commands
            self.pending_write_user_path = parsed_command.args.get("path")
            self.pending_write_content = parsed_command.args.get("content")

        return output_messages

    def confirm_overwrite(self):
        """
        Complete a pending file overwrite (if any) without requiring a user command.
        This is typically called by the GUI's "Overwrite" button.
        """
        if self.pending_write_user_path is None or self.pending_write_content is None:
            return None  # Or some ToolOutput indicating no pending op?

        tool_input = ToolInput(
            operation_name="write",
            args={
                "path": self.pending_write_user_path,
                "content": self.pending_write_content,
                "allow_overwrite": True,
            },
        )
        tool_output = self.file_tool.execute(tool_input)

        response_text = ""
        if tool_output.success:
            response_text = tool_output.message  # Should be like "✅ Saved ..."
            # self.pending_write_user_path = None # These are now cleared by CommandHandler if called via /overwrite
            # self.pending_write_content = None # For confirm_overwrite, we should clear them here.
        else:
            response_text = (
                tool_output.error
                or tool_output.message
                or "⚠️ Error during GUI overwrite."
            )

        sender_label = (
            self.last_model if self.last_model in ["openai", "gemini"] else "openai"
        )
        self.history.add_message(
            role="assistant", content=response_text, sender_provider=sender_label
        )
        logger.info(
            f"Overwrite confirmed via GUI for path: {self.pending_write_user_path or 'N/A'}, result: {response_text}"
        )

        # Clear pending state after confirmation, regardless of success/failure of write itself
        # The tool handles the write, this just clears ChatSession's pending state.
        self.pending_write_user_path = None
        self.pending_write_content = None

        return (sender_label, response_text)  # For GUI to potentially display
