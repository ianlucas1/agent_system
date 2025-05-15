from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, Tuple, List, TYPE_CHECKING
import re
import os  # For os.path.basename
import logging  # Added

from src.tools.base import ToolInput, ToolOutput  # Updated import
from src.tools.file_system import FileManagerTool  # Updated import

# Forward declaration for type hinting ChatSession to avoid circular import
if TYPE_CHECKING:
    from src.core.chat_session import ChatSession  # Updated import

logger = logging.getLogger(__name__)  # Added


class CommandType(Enum):
    READ = auto()
    LIST = auto()
    WRITE = auto()
    OVERWRITE = auto()
    RUN = auto()
    AGENT = auto()
    UNKNOWN = auto()


@dataclass
class Command:
    command_type: CommandType
    args: Any = None


class CommandHandler:
    def __init__(self, file_tool: FileManagerTool):
        self.write_nl_re = re.compile(
            r"^(?:save|write)\s+(?:this|that)\s+to\s+(.+)$", re.IGNORECASE
        )
        self.file_tool = file_tool

    def parse(
        self, user_input: str, chat_log_for_context: List[Tuple[str, str]]
    ) -> Optional[Command]:
        """
        Parses user input to detect slash commands or natural language commands.
        chat_log_for_context is passed in case some natural language commands need context (e.g., "save this").
        Returns a Command object if a command is detected, otherwise None.
        """
        stripped_input = user_input.strip()

        if stripped_input.startswith("/"):
            parts = stripped_input.split(" ", 2)
            cmd_token = parts[0].lower()
            if cmd_token == "/read":
                if len(parts) < 2 or not parts[1].strip():
                    return Command(CommandType.UNKNOWN, args="Usage: /read <filepath>")
                return Command(CommandType.READ, args=parts[1].strip())
            elif cmd_token == "/list":
                dir_path = (
                    parts[1].strip() if len(parts) >= 2 and parts[1].strip() else "."
                )
                return Command(CommandType.LIST, args=dir_path)
            elif cmd_token == "/run" or cmd_token == "/cli":
                if len(parts) < 2 or not parts[1].strip():
                    return Command(CommandType.UNKNOWN, args="Usage: /run <command>")
                # Everything after the first space is treated as the raw command string
                # (allows spaces within the command itself).
                raw_command = stripped_input[len(cmd_token) :].strip()
                return Command(CommandType.RUN, args=raw_command)
            elif cmd_token == "/write":
                if len(parts) < 3:
                    return Command(
                        CommandType.UNKNOWN, args="Usage: /write <filepath> <content>"
                    )
                return Command(CommandType.WRITE, args=(parts[1].strip(), parts[2]))
            elif cmd_token == "/overwrite":
                if len(parts) < 2 or not parts[1].strip():
                    return Command(
                        CommandType.UNKNOWN, args="Usage: /overwrite <filename>"
                    )
                return Command(CommandType.OVERWRITE, args=parts[1].strip())
            elif cmd_token == "/agent":
                if len(parts) < 2 or not parts[1].strip():
                    return Command(CommandType.UNKNOWN, args="Usage: /agent <json-payload>")
                payload = stripped_input[len(cmd_token):].strip()
                return Command(CommandType.AGENT, args=payload)
            else:
                return Command(
                    CommandType.UNKNOWN, args=f"Unknown command: {cmd_token}"
                )

        write_match = self.write_nl_re.match(stripped_input)
        if write_match:
            file_name = write_match.group(1).strip()
            if file_name:
                # For NL write, content needs to be fetched by execute_command from chat_session history
                return Command(CommandType.WRITE, args=(file_name, None))

        low_input = stripped_input.lower()
        if (
            low_input.startswith("what's in")
            or low_input.startswith("what is in")
            or low_input.startswith("list ")
        ):
            # Remove the prefix and leading/trailing whitespace and punctuation
            dir_query = re.sub(
                r"^(what's in( the)?|what is in( the)?|list)\s*",
                "",
                stripped_input,
                flags=re.IGNORECASE,
            ).strip(" .?\t\n\r")
            return Command(CommandType.LIST, args=dir_query if dir_query else ".")

        if (
            low_input.startswith("read ")
            or low_input.startswith("open ")
            or low_input.startswith("show me ")
            or low_input.startswith("show ")
        ):
            if not (" folder" in low_input or " directory" in low_input):
                file_query = re.sub(
                    r"^(read( the)?|open( the)?|show me( the)?|show)\s*",
                    "",
                    stripped_input,
                    flags=re.IGNORECASE,
                ).strip(" ?")
                if file_query:
                    return Command(CommandType.READ, args=file_query)
        return None

    def execute_command(
        self,
        parsed_command: Command,
        chat_session: "ChatSession",
        current_user_input: str,
    ) -> Optional[str]:
        """
        Executes the parsed command using available tools and chat_session state.
        current_user_input is the raw input that triggered this command (for NL write context).
        Returns a string response for the chat, or None if no direct message is generated.
        Manages chat_session.pending_write_user_path and .pending_write_content.
        """
        tool_output = None

        try:
            if parsed_command.command_type == CommandType.READ:
                path = parsed_command.args
                logger.debug(
                    f"Executing READ command for path: {path}"
                )  # Added debug log
                tool_input = ToolInput(operation_name="read", args={"path": path})
                tool_output = self.file_tool.execute(tool_input)

            elif parsed_command.command_type == CommandType.LIST:
                dir_path = parsed_command.args
                logger.debug(
                    f"Executing LIST command for path: {dir_path}"
                )  # Added debug log
                tool_input = ToolInput(operation_name="list", args={"path": dir_path})
                tool_output = self.file_tool.execute(tool_input)

            elif parsed_command.command_type == CommandType.WRITE:
                path, content_to_write = parsed_command.args
                logger.debug(
                    f"Attempting WRITE command for path: {path}"
                )  # Added debug log

                if (
                    content_to_write is None
                ):  # Specific to Natural Language "save this to file.txt"
                    last_assistant_message = None
                    # Iterate from newest, skipping current user "save" command
                    # Accessing chat_session.history.messages directly here
                    for msg_obj in reversed(chat_session.history.messages):
                        if (
                            msg_obj.role == "user"
                            and msg_obj.content == current_user_input
                        ):
                            continue
                        if msg_obj.role == "assistant" and msg_obj.sender_provider in (
                            "openai",
                            "gemini",
                            "collab",
                        ):
                            last_assistant_message = msg_obj.content
                            break
                    if last_assistant_message is None:
                        logger.warning(
                            "NL Write command: No previous assistant message found to save."
                        )  # Added log
                        return "⚠️ No previous assistant message found to save."  # Return directly
                    content_to_write = last_assistant_message
                    logger.debug(
                        f"NL Write command: Found content to save for path {path}"
                    )  # Added log

                tool_input = ToolInput(
                    operation_name="write",
                    args={
                        "path": path,
                        "content": content_to_write,
                        "allow_overwrite": False,
                    },
                )
                tool_output = self.file_tool.execute(tool_input)

                if (
                    not tool_output.success
                    and tool_output.data
                    and tool_output.data.get("status") == "overwrite_required"
                ):
                    chat_session.pending_write_user_path = path
                    chat_session.pending_write_content = content_to_write
                    logger.info(
                        f"Write command for path {path} requires overwrite confirmation."
                    )  # Added log
                    return tool_output.message  # Return warning message directly

            elif parsed_command.command_type == CommandType.OVERWRITE:
                target_file_basename = parsed_command.args
                logger.debug(
                    f"Executing OVERWRITE command for file: {target_file_basename}"
                )  # Added debug log
                if (
                    chat_session.pending_write_user_path is None
                    or chat_session.pending_write_content is None
                ):
                    logger.warning(
                        "Overwrite command: No pending write operation to confirm."
                    )  # Added log
                    return "⚠️ No pending write operation to confirm."  # Return directly

                pending_filename = os.path.basename(
                    chat_session.pending_write_user_path
                )
                if target_file_basename != pending_filename:
                    logger.warning(
                        f"Overwrite command: Mismatch. Target: {target_file_basename}, Pending: {pending_filename}"
                    )  # Added log
                    return f"⚠️ No pending overwrite for `{target_file_basename}` (pending file is `{pending_filename}`)."

                tool_input = ToolInput(
                    operation_name="write",
                    args={
                        "path": chat_session.pending_write_user_path,
                        "content": chat_session.pending_write_content,
                        "allow_overwrite": True,
                    },
                )
                tool_output = self.file_tool.execute(tool_input)
                if tool_output.success:
                    chat_session.pending_write_user_path = None
                    chat_session.pending_write_content = None
                    logger.info(
                        f"Overwrite successful for {pending_filename}"
                    )  # Added log

            elif parsed_command.command_type == CommandType.RUN:
                raw_cmd = parsed_command.args
                logger.debug(f"Executing RUN command: {raw_cmd}")

                from src.tools.registry import ToolRegistry

                shell_tool = ToolRegistry.get("shell_command") or ToolRegistry.get("shell.command")
                if shell_tool is None:
                    from src.tools.shell_command import ShellCommandTool
                    shell_tool = ShellCommandTool()
                logger.info("/run invoked: %s", raw_cmd[:80])
                tool_input = ToolInput(operation_name="run", args={"command": raw_cmd})
                tool_output = shell_tool.execute(tool_input)

            elif parsed_command.command_type == CommandType.AGENT:
                payload = parsed_command.args
                logger.debug("Executing AGENT command with payload: %s", payload)
                import json
                try:
                    data = json.loads(payload)
                    required = {"agent_name", "role_prompt", "task"}
                    if not required.issubset(data):
                        missing = ", ".join(sorted(required - set(data)))
                        return f"⚠️ Missing required keys in /agent payload: {missing}"
                except json.JSONDecodeError:
                    return "⚠️ Syntax error in /agent payload – please supply valid JSON `{...}`"

                from src.tools.registry import ToolRegistry

                agent_tool = ToolRegistry.get("agent.multi")
                if agent_tool is None:
                    from src.tools.multi_agent import MultiAgentTool
                    agent_tool = MultiAgentTool()

                logger.info("/agent invoked: %s", str(data)[:120])
                tool_input = ToolInput(operation_name="spawn", args=data)
                tool_output = agent_tool.execute(tool_input)

                if tool_output.success:
                    agent_name = data.get("agent_name", "Agent")
                    prefix_msg = f"[{agent_name}] {tool_output.message}"
                    tool_output = ToolOutput(success=True, message=prefix_msg, data=tool_output.data)

            elif parsed_command.command_type == CommandType.UNKNOWN:
                logger.warning(
                    f"Unknown command encountered: {parsed_command.args}"
                )  # Added log
                return f"⚠️ {parsed_command.args}"  # Return error message directly

            # Consolidate response/error handling from tool_output if one was generated
            if tool_output:
                if tool_output.success:
                    return tool_output.message
                else:
                    # Log the error from tool_output before returning it
                    logger.error(
                        f"Tool execution failed. Operation: {tool_output.data.get('operation', 'N/A') if tool_output.data else 'N/A'}. Error: {tool_output.error}. Message: {tool_output.message}"
                    )
                    return (
                        tool_output.message
                        or tool_output.error
                        or "⚠️ An unknown error occurred during tool operation."
                    )

            # If command_response_text is still None here, it means a command was recognized but not handled by tool_output
            # This should generally not happen if all command types leading to tool calls are covered.
            if parsed_command.command_type not in [
                CommandType.UNKNOWN
            ]:  # UNKNOWN already returned
                # This case should ideally not be reached if all command types are handled.
                logger.error(
                    f"Command {parsed_command.command_type} was recognized but not fully processed leading to no tool_output."
                )
                return "⚠️ Command recognized but not fully processed."
            # For UNKNOWN, message already returned
            return None

        except Exception as e:
            # Catch-all for unexpected errors during command execution within CommandHandler
            logger.exception(
                f"Unexpected error in CommandHandler.execute_command for command {parsed_command.command_type if parsed_command else 'N/A'}"
            )  # Changed to logger.exception
            return f"⚠️ An unexpected error occurred in CommandHandler: {e}"
