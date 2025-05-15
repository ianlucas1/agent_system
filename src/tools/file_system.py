import os

from .base import Tool, ToolInput, ToolOutput  # Relative import

# Determine base directory for file operations.
# This should be the project root if file_system.py is in src/tools/.
# To make it relative to the project root (one level up from src), use os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# However, for simplicity and if all user paths are relative to project root anyway,
# using a base_dir that assumes operations happen *within* the project root is common.
# For now, let's make base_dir the parent of the 'src' directory.
# This means if the tool is called with "data/file.txt", it resolves to PROJECT_ROOT/data/file.txt
PROJECT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# --- Start of functions moved from file_manager.py ---
def _resolve_path(user_path: str) -> str:
    """
    Resolve a user-provided path to an absolute path.
    It ensures the path is within the PROJECT_ROOT_DIR to prevent directory traversal.
    """
    # Treat user_path as relative to PROJECT_ROOT_DIR unless it's already absolute.
    if os.path.isabs(user_path):
        # If absolute, it must still be within the project root for safety.
        abs_path = os.path.abspath(user_path)
    else:
        abs_path = os.path.abspath(os.path.join(PROJECT_ROOT_DIR, user_path))

    if not abs_path.startswith(PROJECT_ROOT_DIR):
        raise ValueError(
            f"⚠️ Access denied: path `{user_path}` is outside the allowed project directory."
        )
    return abs_path


def read_file_content(
    path: str, max_bytes: int = 100 * 1024, max_lines: int = 200
) -> str:
    abs_path = _resolve_path(path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"⚠️ File not found: `{path}`")
    if os.path.isdir(abs_path):
        raise IsADirectoryError(f"⚠️ `{path}` is a directory, not a file.")
    try:
        with open(abs_path, "rb") as f:
            data = f.read()
    except Exception as e:
        raise OSError(f"⚠️ Error reading `{path}`: {e}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"⚠️ Cannot read `{path}`: file is not readable text.")

    truncated = False
    if len(data) > max_bytes:
        text = data[:max_bytes].decode("utf-8", errors="ignore")
        truncated = True
    else:
        lines = text.splitlines()
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines])
            truncated = True
    if truncated:
        text += "\n[...content truncated...]"
    return text


def list_directory_contents(path: str = ".") -> str:
    abs_path = _resolve_path(path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"⚠️ Directory not found: `{path}`")
    if not os.path.isdir(abs_path):
        raise NotADirectoryError(f"⚠️ `{path}` is not a directory.")
    try:
        entries = os.listdir(abs_path)
    except Exception as e:
        raise OSError(f"⚠️ Error listing directory `{path}`: {e}")
    if not entries:
        return "(empty)"
    entries.sort(key=str.lower)
    result_lines = []
    for entry in entries:
        entry_path = os.path.join(abs_path, entry)
        if os.path.isdir(entry_path):
            display_name = f"📁 {entry}/"
            result_lines.append(f"- {display_name}")
        else:
            size = os.path.getsize(entry_path)
            if size < 1024:
                size_str = f"{size} bytes"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            display_name = f"📄 {entry} ({size_str})"
            result_lines.append(f"- {display_name}")
    return "\n".join(result_lines)


def write_content_to_file(path: str, content: str) -> int:
    abs_path = _resolve_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    try:
        data = content.encode("utf-8")
    except Exception as e:
        raise ValueError(f"⚠️ Failed to encode content for writing: {e}")
    try:
        with open(abs_path, "wb") as f:
            f.write(data)
    except Exception as e:
        raise OSError(f"⚠️ Error writing to `{path}`: {e}")
    return len(data)


# --- End of functions moved from file_manager.py ---


class FileManagerTool(Tool):
    def execute(self, tool_input: ToolInput) -> ToolOutput:
        op_name = tool_input.operation_name
        args = tool_input.args

        try:
            if op_name == "read":
                path = args.get("path")
                if path is None:
                    return ToolOutput(
                        success=False, error="Path not provided for read operation."
                    )
                content = read_file_content(path)  # Uses co-located function
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
                formatted_content = f"Content of `{path}`:\n```{lang}\n{content}\n```"
                return ToolOutput(
                    success=True,
                    message=formatted_content,
                    data={"raw_content": content},
                )

            elif op_name == "list":
                path = args.get("path", ".")
                listing = list_directory_contents(path)  # Uses co-located function
                formatted_listing = f"Contents of `{path}`:\n{listing}"
                return ToolOutput(
                    success=True,
                    message=formatted_listing,
                    data={"listing_text": listing},
                )

            elif op_name == "write":
                path = args.get("path")
                content = args.get("content")
                allow_overwrite = args.get("allow_overwrite", False)

                if path is None:
                    return ToolOutput(
                        success=False, error="Path not provided for write operation."
                    )
                if content is None:
                    return ToolOutput(
                        success=False, error="Content not provided for write operation."
                    )

                abs_target_path = _resolve_path(path)
                if os.path.exists(abs_target_path) and not allow_overwrite:
                    filename = os.path.basename(path)
                    return ToolOutput(
                        success=False,
                        message=f"⚠️ File `{filename}` already exists. Please confirm overwrite or use a different filename.",
                        data={"status": "overwrite_required", "filename": filename},
                    )
                bytes_written = write_content_to_file(
                    path, content
                )  # Uses co-located function
                return ToolOutput(
                    success=True,
                    message=f"✅ Saved `{path}` ({bytes_written} bytes)",
                    data={"bytes_written": bytes_written},
                )
            else:
                return ToolOutput(
                    success=False,
                    error=f"Unknown operation for FileManagerTool: {op_name}",
                )

        except (
            FileNotFoundError,
            IsADirectoryError,
            NotADirectoryError,
            ValueError,
            OSError,
        ) as e_fm:
            return ToolOutput(success=False, error=str(e_fm))
        except Exception as e_general:
            return ToolOutput(
                success=False,
                error=f"An unexpected error occurred in FileManagerTool: {e_general}",
            )
