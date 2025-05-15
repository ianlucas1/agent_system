"""
chat_session.py - Defines the ChatSession class for managing multi-turn conversations,
command parsing, and routing to language models and file operations.
"""
import os
from dotenv import load_dotenv
import importlib

# Import the file manager module for file operations
try:
    from . import file_manager
except ImportError:
    import file_manager

class ChatSession:
    """
    ChatSession manages a conversation with one or two LLMs, including message history,
    command parsing (/read, /write, /list, /overwrite), and integration with file system and optional A2A collaboration.
    """
    def __init__(self):
        # Initialize API clients and state
        load_dotenv()
        self.openai_client = None
        self.gemini_client = None
        self.openai_available = False
        self.gemini_available = False
        self._init_clients()
        # Conversation histories for each agent (list of {'role': ..., 'content': ...})
        # Include an initial system prompt describing capabilities
        system_prompt = ("You are a helpful AI assistant. You have access to a local project file system. "
                         "You can read files, write files (with user confirmation), and list directories when asked.")
        self.openai_history = [{"role": "system", "content": system_prompt}]
        self.gemini_history = [{"role": "system", "content": system_prompt}]
        # Combined chat log for display (list of (sender, content))
        # sender is one of "user", "openai", "gemini", "collab"
        self.chat_log = []
        # Pending write operation data (for overwrite confirmation)
        self.pending_write_path = None
        self.pending_write_content = None
        # Track last model used for context synchronization
        self.last_model = None

    def _init_clients(self):
        """Initialize OpenAI and Google Gemini API clients based on API keys in environment."""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        # Initialize OpenAI client
        if openai_api_key:
            try:
                from openai import OpenAI
                # Instantiate a typed client instance (recommended ≥ 1.0.0)
                self.openai_client = OpenAI(api_key=openai_api_key)
                self.openai_available = True
            except ImportError:
                self.openai_client = None
                self.openai_available = False
            except Exception as e:
                self.openai_client = None
                self.openai_available = False
        else:
            self.openai_client = None
            self.openai_available = False
        # Initialize Google Gemini client
        if google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-2.5-pro-preview-05-06')
                self.gemini_available = True
            except ImportError:
                self.gemini_client = None
                self.gemini_available = False
            except Exception as e:
                self.gemini_client = None
                self.gemini_available = False
        else:
            self.gemini_client = None
            self.gemini_available = False

    def process_user_message(self, user_input: str, model_choice: str = "openai", use_a2a: bool = False):
        """
        Process a user input message, handle commands or get response from model(s).
        model_choice: "openai", "gemini", or "both".
        use_a2a: if True and model_choice=="both", engage collaborative A2A mode.
        Returns a list of (sender, content) tuples representing the assistant responses generated.
        """
        user_input = user_input.strip()
        # Determine if switching model for context sync
        if self.last_model and model_choice != self.last_model:
            # Sync conversation history to the new model's history list using unified chat_log
            self._sync_history_to(model_choice)
        # Track the current model as last used
        self.last_model = model_choice

        # Check and handle file system commands
        is_command = False
        command_type = None
        cmd_args = None
        output_messages = []

        # Slash commands explicitly
        if user_input.startswith("/"):
            is_command = True
            parts = user_input.split(" ", 2)
            cmd = parts[0].lower()
            if cmd == "/read":
                command_type = "read"
                if len(parts) < 2 or parts[1] == "":
                    output_messages.append(("openai" if model_choice != "gemini" else "gemini",
                                             "⚠️ Usage: /read <filepath>"))
                    # Log user command and response
                    self.chat_log.append(("user", user_input))
                    self.chat_log.append((output_messages[0][0], output_messages[0][1]))
                    for history in (self.openai_history, self.gemini_history):
                        history.append({"role": "user", "content": user_input})
                        history.append({"role": "assistant", "content": output_messages[0][1]})
                    return output_messages
                path = parts[1].strip()
                cmd_args = path
            elif cmd == "/list":
                command_type = "list"
                dir_path = "."
                if len(parts) >= 2 and parts[1] != "":
                    dir_path = parts[1].strip()
                cmd_args = dir_path
            elif cmd == "/write":
                command_type = "write"
                if len(parts) < 3:
                    output_messages.append(("openai" if model_choice != "gemini" else "gemini",
                                             "⚠️ Usage: /write <filepath> <content>"))
                    self.chat_log.append(("user", user_input))
                    self.chat_log.append((output_messages[0][0], output_messages[0][1]))
                    for history in (self.openai_history, self.gemini_history):
                        history.append({"role": "user", "content": user_input})
                        history.append({"role": "assistant", "content": output_messages[0][1]})
                    return output_messages
                path = parts[1].strip()
                content_to_write = parts[2]
                cmd_args = (path, content_to_write)
            elif cmd == "/overwrite":
                command_type = "overwrite"
                target_file = parts[1].strip() if len(parts) >= 2 else ""
                cmd_args = target_file
            else:
                is_command = False
        else:
            # Natural language command triggers
            low = user_input.lower()
            if ("save this to " in low) or ("save that to " in low) or ("write this to " in low):
                import re
                m = re.match(r'^(?:save|write)\s+(?:this|that)\s+to\s+(.+)$', low)
                if m:
                    command_type = "write"
                    file_name = m.group(1).strip()
                    if file_name:
                        last_assistant = None
                        for sender, content in reversed(self.chat_log):
                            if sender in ("openai", "gemini", "collab"):
                                last_assistant = content
                                break
                        if last_assistant is None:
                            output_messages.append(( "openai" if model_choice != "gemini" else "gemini",
                                                      "⚠️ No content available to save."))
                            self.chat_log.append(("user", user_input))
                            self.chat_log.append((output_messages[0][0], output_messages[0][1]))
                            for history in (self.openai_history, self.gemini_history):
                                history.append({"role": "user", "content": user_input})
                                history.append({"role": "assistant", "content": output_messages[0][1]})
                            return output_messages
                        cmd_args = (file_name, last_assistant)
                        is_command = True
            if not is_command:
                if low.startswith("what's in") or low.startswith("what is in"):
                    dir_query = user_input
                    for prefix in ["what's in the", "what is in the", "what's in", "what is in"]:
                        if low.startswith(prefix):
                            dir_query = user_input[len(prefix):].strip()
                            break
                    dir_query = dir_query.rstrip(" ?.")
                    if dir_query.lower().endswith(" folder"):
                        dir_query = dir_query[:-len(" folder")].strip()
                    if dir_query.lower().endswith(" directory"):
                        dir_query = dir_query[:-len(" directory")].strip()
                    if dir_query == "":
                        dir_query = "."
                    command_type = "list"
                    cmd_args = dir_query
                    is_command = True
                elif low.startswith("list "):
                    dir_query = user_input[5:].strip()
                    if dir_query == "":
                        dir_query = "."
                    command_type = "list"
                    cmd_args = dir_query
                    is_command = True
                if not is_command:
                    if low.startswith("read ") or low.startswith("open ") or low.startswith("show me ") or low.startswith("show "):
                        if " folder" in low or " directory" in low:
                            dir_query = user_input
                            for prefix in ["open the", "open", "show me the", "show me", "show the", "show", "read the", "read"]:
                                if low.startswith(prefix):
                                    dir_query = user_input[len(prefix):].strip()
                                    break
                            dir_query = dir_query.rstrip(" .?")
                            if dir_query.lower().endswith(" folder"):
                                dir_query = dir_query[:-len(" folder")].strip()
                            if dir_query.lower().endswith(" directory"):
                                dir_query = dir_query[:-len(" directory")].strip()
                            if dir_query == "":
                                dir_query = "."
                            command_type = "list"
                            cmd_args = dir_query
                            is_command = True
                        else:
                            file_query = user_input
                            for prefix in ["open the", "open", "read the", "read", "show me the", "show me", "show"]:
                                if low.startswith(prefix):
                                    file_query = user_input[len(prefix):].strip()
                                    break
                            file_query = file_query.strip(" ?")
                            if file_query != "":
                                command_type = "read"
                                cmd_args = file_query
                                is_command = True

        if is_command and command_type:
            self.chat_log.append(("user", user_input))
            self.openai_history.append({"role": "user", "content": user_input})
            self.gemini_history.append({"role": "user", "content": user_input})
            try:
                if command_type == "read":
                    path = cmd_args
                    content = file_manager.read_file(path)
                    _, ext = os.path.splitext(path)
                    lang = ""
                    if ext:
                        ext = ext.lower()
                        if ext in [".py", ".pyw"]:
                            lang = "python"
                        elif ext in [".json"]:
                            lang = "json"
                        elif ext in [".md"]:
                            lang = "markdown"
                        elif ext in [".yaml", ".yml"]:
                            lang = "yaml"
                        elif ext in [".csv"]:
                            lang = ""
                    response_text = f"Content of `{path}`:\n```{lang}\n{content}\n```"
                    sender_label = "openai" if model_choice != "gemini" else "gemini"
                    if model_choice == "both":
                        sender_label = "openai"
                    self.chat_log.append((sender_label, response_text))
                    self.openai_history.append({"role": "assistant", "content": response_text})
                    self.gemini_history.append({"role": "assistant", "content": response_text})
                    output_messages.append((sender_label, response_text))
                elif command_type == "list":
                    dir_path = cmd_args
                    listing = file_manager.list_dir(dir_path)
                    response_text = f"Contents of `{dir_path}`:\n{listing}"
                    sender_label = "openai" if model_choice != "gemini" else "gemini"
                    if model_choice == "both":
                        sender_label = "openai"
                    self.chat_log.append((sender_label, response_text))
                    self.openai_history.append({"role": "assistant", "content": response_text})
                    self.gemini_history.append({"role": "assistant", "content": response_text})
                    output_messages.append((sender_label, response_text))
                elif command_type == "write":
                    path, content_to_write = cmd_args
                    abs_target = file_manager._resolve_path(path)
                    if os.path.exists(abs_target):
                        self.pending_write_path = abs_target
                        self.pending_write_content = content_to_write
                        filename = os.path.basename(path)
                        warning_msg = (f"⚠️ File `{filename}` already exists. Please confirm overwrite by typing `/overwrite {filename}` "
                                       f"or use a different filename.")
                        sender_label = "openai" if model_choice != "gemini" else "gemini"
                        if model_choice == "both":
                            sender_label = "openai"
                        self.chat_log.append((sender_label, warning_msg))
                        self.openai_history.append({"role": "assistant", "content": warning_msg})
                        self.gemini_history.append({"role": "assistant", "content": warning_msg})
                        output_messages.append((sender_label, warning_msg))
                    else:
                        bytes_written = file_manager.write_file(path, content_to_write)
                        success_msg = f"✅ Saved `{path}` ({bytes_written} bytes)"
                        sender_label = "openai" if model_choice != "gemini" else "gemini"
                        if model_choice == "both":
                            sender_label = "openai"
                        self.chat_log.append((sender_label, success_msg))
                        self.openai_history.append({"role": "assistant", "content": success_msg})
                        self.gemini_history.append({"role": "assistant", "content": success_msg})
                        output_messages.append((sender_label, success_msg))
                elif command_type == "overwrite":
                    target_file = cmd_args
                    if self.pending_write_path is None:
                        error_msg = "⚠️ No pending write operation to confirm."
                        sender_label = "openai" if model_choice != "gemini" else "gemini"
                        if model_choice == "both":
                            sender_label = "openai"
                        self.chat_log.append((sender_label, error_msg))
                        self.openai_history.append({"role": "assistant", "content": error_msg})
                        self.gemini_history.append({"role": "assistant", "content": error_msg})
                        output_messages.append((sender_label, error_msg))
                    else:
                        pending_name = os.path.basename(self.pending_write_path)
                        if target_file and os.path.basename(target_file) != pending_name:
                            error_msg = f"⚠️ No pending overwrite for `{target_file}` (pending file is `{pending_name}`)."
                            sender_label = "openai" if model_choice != "gemini" else "gemini"
                            if model_choice == "both":
                                sender_label = "openai"
                            self.chat_log.append((sender_label, error_msg))
                            self.openai_history.append({"role": "assistant", "content": error_msg})
                            self.gemini_history.append({"role": "assistant", "content": error_msg})
                            output_messages.append((sender_label, error_msg))
                        else:
                            rel_path = os.path.relpath(self.pending_write_path, file_manager.base_dir)
                            bytes_written = file_manager.write_file(rel_path, self.pending_write_content)
                            success_msg = f"✅ Saved `{rel_path}` ({bytes_written} bytes)"
                            sender_label = "openai" if model_choice != "gemini" else "gemini"
                            if model_choice == "both":
                                sender_label = "openai"
                            self.chat_log.append((sender_label, success_msg))
                            self.openai_history.append({"role": "assistant", "content": success_msg})
                            self.gemini_history.append({"role": "assistant", "content": success_msg})
                            output_messages.append((sender_label, success_msg))
                            self.pending_write_path = None
                            self.pending_write_content = None
            except Exception as e:
                error_msg = str(e) if str(e) else "⚠️ An unknown error occurred during file operation."
                sender_label = "openai" if model_choice != "gemini" else "gemini"
                if model_choice == "both":
                    sender_label = "openai"
                self.chat_log.append((sender_label, error_msg))
                self.openai_history.append({"role": "assistant", "content": error_msg})
                self.gemini_history.append({"role": "assistant", "content": error_msg})
                output_messages.append((sender_label, error_msg))
            return output_messages

        # Not a file command: handle with model(s)
        self.chat_log.append(("user", user_input))
        if model_choice == "openai":
            self.openai_history.append({"role": "user", "content": user_input})
        elif model_choice == "gemini":
            self.gemini_history.append({"role": "user", "content": user_input})
        elif model_choice == "both":
            self.openai_history.append({"role": "user", "content": user_input})
            self.gemini_history.append({"role": "user", "content": user_input})
        if model_choice == "openai" and not self.openai_available:
            error_msg = "⚠️ OpenAI model is not available."
            self.chat_log.append(("openai", error_msg))
            output_messages.append(("openai", error_msg))
            self.openai_history.append({"role": "assistant", "content": error_msg})
            return output_messages
        if model_choice == "gemini" and not self.gemini_available:
            error_msg = "⚠️ Gemini model is not available."
            self.chat_log.append(("gemini", error_msg))
            output_messages.append(("gemini", error_msg))
            self.gemini_history.append({"role": "assistant", "content": error_msg})
            return output_messages
        if model_choice == "both":
            if not self.openai_available or not self.gemini_available:
                error_msg = "⚠️ Cannot use both models: "
                if not self.openai_available:
                    error_msg += "OpenAI not initialized. "
                if not self.gemini_available:
                    error_msg += "Gemini not initialized."
                sender_label = "openai"
                self.chat_log.append((sender_label, error_msg))
                output_messages.append((sender_label, error_msg))
                self.openai_history.append({"role": "assistant", "content": error_msg})
                self.gemini_history.append({"role": "assistant", "content": error_msg})
                return output_messages

        if model_choice == "openai":
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self.openai_history
                )
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"Error communicating with OpenAI: {e}"
            self.openai_history.append({"role": "assistant", "content": answer})
            self.chat_log.append(("openai", answer))
            output_messages.append(("openai", answer))
        elif model_choice == "gemini":
            try:
                prompt = ""
                for msg in self.gemini_history:
                    role = msg["role"]
                    content = msg["content"]
                    if role == "system":
                        prompt += f"System: {content}\n\n"
                    elif role == "user":
                        prompt += f"User: {content}\n"
                    elif role == "assistant":
                        prompt += f"Assistant: {content}\n"
                prompt += "Assistant:"
                response = self.gemini_client.generate_content(prompt)
                answer = response.text
            except Exception as e:
                answer = f"Error communicating with Gemini: {e}"
            self.gemini_history.append({"role": "assistant", "content": answer})
            self.chat_log.append(("gemini", answer))
            output_messages.append(("gemini", answer))
        elif model_choice == "both":
            if use_a2a:
                try:
                    from . import a2a_collaboration
                except ImportError:
                    try:
                        import a2a_collaboration
                    except ImportError:
                        collab_answer = "⚠️ A2A collaboration mode is not available (library not installed)."
                        self.chat_log.append(("openai", collab_answer))
                        output_messages.append(("openai", collab_answer))
                        self.openai_history.append({"role": "assistant", "content": collab_answer})
                        self.gemini_history.append({"role": "assistant", "content": collab_answer})
                        return output_messages
                try:
                    collab_answer = a2a_collaboration.run(user_input, self.openai_client, self.gemini_client)
                except Exception as e:
                    collab_answer = f"Error during A2A collaboration: {e}"
                self.openai_history.append({"role": "assistant", "content": collab_answer})
                self.gemini_history.append({"role": "assistant", "content": collab_answer})
                self.chat_log.append(("collab", collab_answer))
                output_messages.append(("collab", collab_answer))
            else:
                try:
                    response_o = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=self.openai_history
                    )
                    answer_o = response_o.choices[0].message.content
                except Exception as e:
                    answer_o = f"Error communicating with OpenAI: {e}"
                try:
                    prompt = ""
                    for msg in self.gemini_history:
                        role = msg["role"]
                        content = msg["content"]
                        if role == "system":
                            prompt += f"System: {content}\\n\\n"
                        elif role == "user":
                            prompt += f"User: {content}\\n"
                        elif role == "assistant":
                            prompt += f"Assistant: {content}\\n"
                    prompt += "Assistant:"
                    response_g = self.gemini_client.generate_content(prompt)
                    answer_g = response_g.text
                except Exception as e:
                    answer_g = f"Error communicating with Gemini: {e}"
                self.openai_history.append({"role": "assistant", "content": answer_o})
                self.gemini_history.append({"role": "assistant", "content": answer_g})
                self.chat_log.append(("openai", answer_o))
                self.chat_log.append(("gemini", answer_g))
                output_messages.append(("openai", answer_o))
                output_messages.append(("gemini", answer_g))
        return output_messages

    def _sync_history_to(self, target_model: str):
        """
        Synchronize the conversation history into the target model's history list using the unified chat_log.
        Ensures that when switching models, the new model sees the full conversation.
        """
        unified_messages = []
        if self.openai_history and self.openai_history[0]["role"] == "system":
            system_prompt = self.openai_history[0]["content"]
            unified_messages.append({"role": "system", "content": system_prompt})
        for sender, content in self.chat_log:
            if sender == "user":
                unified_messages.append({"role": "user", "content": content})
            else:
                unified_messages.append({"role": "assistant", "content": content})
        if target_model == "openai":
            self.openai_history = unified_messages.copy()
        elif target_model == "gemini":
            self.gemini_history = unified_messages.copy()
        elif target_model == "both":
            self.openai_history = unified_messages.copy()
            self.gemini_history = unified_messages.copy()

    def confirm_overwrite(self):
        """
        Complete a pending file overwrite (if any) without requiring a user command.
        Used in a GUI context where the user confirms via button rather than typing /overwrite.
        Returns a tuple (sender, content) for the resulting assistant message, or None if no pending operation.
        """
        if self.pending_write_path is None:
            return None
        pending_name = os.path.basename(self.pending_write_path)
        try:
            rel_path = os.path.relpath(self.pending_write_path, file_manager.base_dir)
            bytes_written = file_manager.write_file(rel_path, self.pending_write_content)
            success_msg = f"✅ Saved `{rel_path}` ({bytes_written} bytes)"
        except Exception as e:
            success_msg = str(e) if str(e) else f"⚠️ Error writing to `{pending_name}`"
        sender_label = "openai"
        if self.last_model == "gemini":
            sender_label = "gemini"
        elif self.last_model == "both":
            sender_label = "openai"
        self.chat_log.append((sender_label, success_msg))
        self.openai_history.append({"role": "assistant", "content": success_msg})
        self.gemini_history.append({"role": "assistant", "content": success_msg})
        self.pending_write_path = None
        self.pending_write_content = None
        return (sender_label, success_msg)
