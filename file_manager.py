"""
file_manager.py - Provides safe file system operations (/read, /write, /list) restricted to project directory.
"""
import os

# Determine base directory for file operations (project root)
base_dir = os.path.abspath(os.path.dirname(__file__))

def _resolve_path(user_path: str) -> str:
    """
    Resolve a user-provided path to an absolute path within the allowed base_dir.
    Raises ValueError if the resolved path is outside the base directory.
    """
    # If the user path is absolute, use it directly, otherwise join with base_dir
    if os.path.isabs(user_path):
        abs_path = os.path.abspath(user_path)
    else:
        abs_path = os.path.abspath(os.path.join(base_dir, user_path))
    # Prevent access outside the base_dir
    if not abs_path.startswith(base_dir):
        raise ValueError("⚠️ Access denied: path is outside the allowed directory.")
    return abs_path

def read_file(path: str, max_bytes: int = 100*1024, max_lines: int = 200) -> str:
    """
    Read the file at the given path (relative to base_dir) in text mode.
    Returns the file content as a string, potentially truncated with a marker if large.
    Raises FileNotFoundError if file not found, IsADirectoryError if path is a directory,
    ValueError for invalid access, or OSError for other I/O issues.
    """
    abs_path = _resolve_path(path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"⚠️ File not found: `{path}`")
    if os.path.isdir(abs_path):
        raise IsADirectoryError(f"⚠️ `{path}` is a directory, not a file.")
    try:
        # Read file in binary first to safely handle decoding
        with open(abs_path, "rb") as f:
            data = f.read()
    except Exception as e:
        raise OSError(f"⚠️ Error reading `{path}`: {e}")
    # Try to decode as UTF-8
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        # Not a text file (binary or unknown encoding)
        raise ValueError(f"⚠️ Cannot read `{path}`: file is not readable text.")
    # Truncate content if too large
    truncated = False
    if len(data) > max_bytes:
        # truncate by bytes
        text = data[:max_bytes].decode('utf-8', errors='ignore')
        truncated = True
    else:
        # also check line count
        lines = text.splitlines()
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines])
            truncated = True
    if truncated:
        text += "\n[...content truncated...]"
    return text

def list_dir(path: str = ".") -> str:
    """
    List contents of the given directory (relative to base_dir).
    Returns a formatted string listing immediate files and subdirectories.
    Raises FileNotFoundError if path not found, NotADirectoryError if not a directory, or ValueError for invalid access.
    """
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
    # Sort entries alphabetically
    entries.sort(key=str.lower)
    result_lines = []
    for entry in entries:
        entry_path = os.path.join(abs_path, entry)
        if os.path.isdir(entry_path):
            display_name = f"📁 {entry}/"
            result_lines.append(f"- {display_name}")
        else:
            size = os.path.getsize(entry_path)
            # Format size in human-readable form
            if size < 1024:
                size_str = f"{size} bytes"
            elif size < 1024*1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            display_name = f"📄 {entry} ({size_str})"
            result_lines.append(f"- {display_name}")
    return "\n".join(result_lines)

def write_file(path: str, content: str) -> int:
    """
    Write the given content to the file at the specified path (relative to base_dir), overwriting or creating the file.
    Returns the number of bytes written.
    Raises ValueError for invalid access or other I/O errors.
    """
    abs_path = _resolve_path(path)
    # Ensure the directory exists (if writing to subdir)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    try:
        data = content.encode('utf-8')
    except Exception as e:
        raise ValueError(f"⚠️ Failed to encode content for writing: {e}")
    try:
        with open(abs_path, "wb") as f:
            f.write(data)
    except Exception as e:
        raise OSError(f"⚠️ Error writing to `{path}`: {e}")
    return len(data)
