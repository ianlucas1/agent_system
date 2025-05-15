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
        # Default model names (can be overridden by GUI)
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro-preview-05-06")

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
                self.gemini_client = genai.GenerativeModel(self.gemini_model)
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

    def process_user_message(self, user_input: str, model_choice: str = "openai", specific_model_name: str = None, use_a2a: bool = False):
        """
        Process a user input message, handle commands or get response from model(s).
        model_choice: "openai" or "gemini" (acts as provider based on GUI selection).
        specific_model_name: The exact model name selected in the GUI (e.g., "gpt-4.1", "gemini-2.5-pro-preview-05-06")
        use_a2a: Currently unused due to single model selection GUI.
        Returns a list of (sender, content) tuples representing the assistant responses generated.
        """
        user_input = user_input.strip()

        # Update the relevant model in the session if a specific one is passed
        if specific_model_name:
            if model_choice == "openai":
                self.openai_model = specific_model_name
            elif model_choice == "gemini":
                # Re-initialize Gemini client ONLY if model name changes AND client is available
                if self.gemini_available and self.gemini_model != specific_model_name:
                    try:
                        import google.generativeai as genai
                        self.gemini_client = genai.GenerativeModel(specific_model_name)
                        self.gemini_model = specific_model_name # Update after successful re-init
                    except Exception as e:
                        # If re-init fails, mark Gemini as unavailable for this call to prevent further errors
                        # self.gemini_available = False # Option: or just let the error propagate
                        print(f"Error re-initializing Gemini client for model {specific_model_name}: {e}")
                        # Potentially add a message to output_messages here
                elif not self.gemini_available: # If it wasn't available to begin with, just set the name
                     self.gemini_model = specific_model_name
                else: # It is available and name is the same, no change needed
                    pass
        
        # Determine if switching model for context sync (less relevant with single model choice GUI but kept for robustness)
        if self.last_model and model_choice != self.last_model:
            self._sync_history_to(model_choice)
        self.last_model = model_choice

        # Check and handle file system commands
        is_command = False
        command_type = None
        cmd_args = None
        output_messages = []

        # Slash commands explicitly (sender_label determined by model_choice)
        sender_for_commands = model_choice # "openai" or "gemini"

        if user_input.startswith("/"):
            is_command = True
            parts = user_input.split(" ", 2)
            cmd = parts[0].lower()
            if cmd == "/read":
                command_type = "read"
                if len(parts) < 2 or parts[1] == "":
                    output_messages.append((sender_for_commands, "⚠️ Usage: /read <filepath>"))
                    # Log user command and response
                    self.chat_log.append(("user", user_input))
                    self.chat_log.append((sender_for_commands, output_messages[0][1]))
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
                    output_messages.append((sender_for_commands, "⚠️ Usage: /write <filepath> <content>"))
                    self.chat_log.append(("user", user_input))
                    self.chat_log.append((sender_for_commands, output_messages[0][1]))
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
                is_command = False # Not a recognized slash command
        else:
            # Natural language command triggers (simplified, sender_for_commands will be used)
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
                            if sender in ("openai", "gemini"):
                                last_assistant = content
                                break
                        if last_assistant is None:
                            output_messages.append((sender_for_commands, "⚠️ No content available to save."))
                            self.chat_log.append(("user", user_input))
                            self.chat_log.append((sender_for_commands, output_messages[0][1]))
                            for history in (self.openai_history, self.gemini_history):
                                history.append({"role": "user", "content": user_input})
                                history.append({"role": "assistant", "content": output_messages[0][1]})
                            return output_messages
                        cmd_args = (file_name, last_assistant)
                        is_command = True
            if not is_command:
                if low.startswith("what's in") or low.startswith("what is in") or low.startswith("list "):
                    # Simplified parsing for list
                    dir_query = user_input.lower().replace("what's in the", "").replace("what is in the", "").replace("what's in", "").replace("what is in", "").replace("list ", "").strip(" ?.folderdirectory")
                    cmd_args = dir_query if dir_query else "."
                    command_type = "list"
                    is_command = True
                elif low.startswith("read ") or low.startswith("open ") or low.startswith("show me ") or low.startswith("show "):
                    if not (" folder" in low or " directory" in low): # Avoid conflict with list
                        # Simplified parsing for read
                        file_query = user_input.lower().replace("open the", "").replace("open", "").replace("read the", "").replace("read", "").replace("show me the", "").replace("show me", "").replace("show", "").strip(" ?")
                        if file_query:
                            cmd_args = file_query
                            command_type = "read"
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
                    self.chat_log.append((sender_for_commands, response_text))
                    self.openai_history.append({"role": "assistant", "content": response_text})
                    self.gemini_history.append({"role": "assistant", "content": response_text})
                    output_messages.append((sender_for_commands, response_text))
                elif command_type == "list":
                    dir_path = cmd_args
                    listing = file_manager.list_dir(dir_path)
                    response_text = f"Contents of `{dir_path}`:\n{listing}"
                    self.chat_log.append((sender_for_commands, response_text))
                    self.openai_history.append({"role": "assistant", "content": response_text})
                    self.gemini_history.append({"role": "assistant", "content": response_text})
                    output_messages.append((sender_for_commands, response_text))
                elif command_type == "write":
                    path, content_to_write = cmd_args
                    abs_target = file_manager._resolve_path(path)
                    if os.path.exists(abs_target):
                        self.pending_write_path = abs_target
                        self.pending_write_content = content_to_write
                        filename = os.path.basename(path)
                        warning_msg = (f"⚠️ File `{filename}` already exists. Please confirm overwrite by typing `/overwrite {filename}` "
                                       f"or use a different filename.")
                        self.chat_log.append((sender_for_commands, warning_msg))
                        self.openai_history.append({"role": "assistant", "content": warning_msg})
                        self.gemini_history.append({"role": "assistant", "content": warning_msg})
                        output_messages.append((sender_for_commands, warning_msg))
                    else:
                        bytes_written = file_manager.write_file(path, content_to_write)
                        success_msg = f"✅ Saved `{path}` ({bytes_written} bytes)"
                        self.chat_log.append((sender_for_commands, success_msg))
                        self.openai_history.append({"role": "assistant", "content": success_msg})
                        self.gemini_history.append({"role": "assistant", "content": success_msg})
                        output_messages.append((sender_for_commands, success_msg))
                elif command_type == "overwrite":
                    target_file = cmd_args
                    if self.pending_write_path is None:
                        error_msg = "⚠️ No pending write operation to confirm."
                        self.chat_log.append((sender_for_commands, error_msg))
                        self.openai_history.append({"role": "assistant", "content": error_msg})
                        self.gemini_history.append({"role": "assistant", "content": error_msg})
                        output_messages.append((sender_for_commands, error_msg))
                    else:
                        pending_name = os.path.basename(self.pending_write_path)
                        if target_file and os.path.basename(target_file) != pending_name:
                            error_msg = f"⚠️ No pending overwrite for `{target_file}` (pending file is `{pending_name}`)."
                            self.chat_log.append((sender_for_commands, error_msg))
                            self.openai_history.append({"role": "assistant", "content": error_msg})
                            self.gemini_history.append({"role": "assistant", "content": error_msg})
                            output_messages.append((sender_for_commands, error_msg))
                        else:
                            rel_path = os.path.relpath(self.pending_write_path, file_manager.base_dir)
                            bytes_written = file_manager.write_file(rel_path, self.pending_write_content)
                            success_msg = f"✅ Saved `{rel_path}` ({bytes_written} bytes)"
                            self.chat_log.append((sender_for_commands, success_msg))
                            self.openai_history.append({"role": "assistant", "content": success_msg})
                            self.gemini_history.append({"role": "assistant", "content": success_msg})
                            output_messages.append((sender_for_commands, success_msg))
                            self.pending_write_path = None
                            self.pending_write_content = None
            except Exception as e:
                error_msg = str(e) if str(e) else "⚠️ An unknown error occurred during file operation."
                self.chat_log.append((sender_for_commands, error_msg))
                self.openai_history.append({"role": "assistant", "content": error_msg})
                self.gemini_history.append({"role": "assistant", "content": error_msg})
                output_messages.append((sender_for_commands, error_msg))
            return output_messages

        # Not a file command: handle with selected model provider
        self.chat_log.append(("user", user_input))

        if model_choice == "openai":
            self.openai_history.append({"role": "user", "content": user_input})
            if not self.openai_available:
                error_msg = "⚠️ OpenAI model is not available."
                self.chat_log.append(("openai", error_msg))
                output_messages.append(("openai", error_msg))
                self.openai_history.append({"role": "assistant", "content": error_msg})
                return output_messages
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model, # Uses the updated self.openai_model
                    messages=self.openai_history
                )
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"Error communicating with OpenAI: {e}"
            self.openai_history.append({"role": "assistant", "content": answer})
            self.chat_log.append(("openai", answer))
            output_messages.append(("openai", answer))

        elif model_choice == "gemini":
            self.gemini_history.append({"role": "user", "content": user_input})
            if not self.gemini_available:
                error_msg = "⚠️ Gemini model is not available."
                self.chat_log.append(("gemini", error_msg))
                output_messages.append(("gemini", error_msg))
                self.gemini_history.append({"role": "assistant", "content": error_msg})
                return output_messages
            try:
                prompt = "" # Construct prompt for Gemini from its history
                for msg in self.gemini_history:
                    role = msg["role"]
                    content = msg["content"]
                    if role == "system": prompt += f"System: {content}\n\n"
                    elif role == "user": prompt += f"User: {content}\n"
                    elif role == "assistant": prompt += f"Assistant: {content}\n"
                prompt += "Assistant:"
                
                # Gemini client should have been re-initialized if model changed
                if not self.gemini_client: # Double check if it became none due to re-init error
                    raise Exception("Gemini client not initialized after model selection.")

                response = self.gemini_client.generate_content(prompt)
                answer = response.text
            except Exception as e:
                answer = f"Error communicating with Gemini: {e}"
            self.gemini_history.append({"role": "assistant", "content": answer})
            self.chat_log.append(("gemini", answer))
            output_messages.append(("gemini", answer))
        
        return output_messages

    def _sync_history_to(self, target_model: str):
        """
        Synchronize the conversation history into the target model's history list using the unified chat_log.
        """
        unified_messages = []
        # Use OpenAI's system prompt as the base if available, otherwise a generic one
        system_prompt_content = "You are a helpful AI assistant."
        if self.openai_history and self.openai_history[0]["role"] == "system":
            system_prompt_content = self.openai_history[0]["content"]
        elif self.gemini_history and self.gemini_history[0]["role"] == "system": # Fallback to Gemini's
            system_prompt_content = self.gemini_history[0]["content"]
        
        unified_messages.append({"role": "system", "content": system_prompt_content})

        for sender, content in self.chat_log:
            if sender == "user":
                unified_messages.append({"role": "user", "content": content})
            elif sender == "openai" or sender == "gemini": # Treat both as assistant for history
                unified_messages.append({"role": "assistant", "content": content})
        
        if target_model == "openai":
            self.openai_history = unified_messages.copy()
        elif target_model == "gemini":
            self.gemini_history = unified_messages.copy()
        # No "both" case needed with current GUI

    def confirm_overwrite(self):
        """
        Complete a pending file overwrite (if any) without requiring a user command.
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
        
        # Determine sender based on the last model that was active
        sender_label = self.last_model if self.last_model in ["openai", "gemini"] else "openai"

        self.chat_log.append((sender_label, success_msg))
        # Log to both histories for robustness, though only one is active at a time
        self.openai_history.append({"role": "assistant", "content": success_msg})
        self.gemini_history.append({"role": "assistant", "content": success_msg})
        self.pending_write_path = None
        self.pending_write_content = None
        return (sender_label, success_msg)
