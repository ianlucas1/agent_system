import json
import os
from pathlib import Path


class ContextBusFullError(Exception):
    """Raised when the context store exceeds the maximum allowed size."""
    pass


class ContextBus:
    """
    A simple file-backed key-value store for sharing context across agents.

    Loads and persists data to a JSON file with atomic writes.
    """

    _SIZE_LIMIT_BYTES = 200 * 1024  # 200 KB

    def __init__(self, path: Path | str | None = None) -> None:
        # Determine file path
        if path is None:
            # Default to agent_workspace/context.json relative to project root
            self.path = Path(os.getcwd()) / "agent_workspace" / "context.json"
        else:
            self.path = Path(path)
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> dict[str, str]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def _write_data(self, data: dict[str, str]) -> None:
        # Serialize to JSON bytes
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        # Enforce size limit
        if len(content) > self._SIZE_LIMIT_BYTES:
            raise ContextBusFullError(
                f"ContextBus store exceeds size limit: {len(content)} bytes > {self._SIZE_LIMIT_BYTES} bytes"
            )
        # Write atomically
        tmp_path = self.path.parent / (self.path.name + ".tmp")
        with open(tmp_path, "wb") as tmp_file:
            tmp_file.write(content)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, self.path)

    def get(self, key: str) -> str | None:
        """Retrieve the value for *key*, or None if absent."""
        data = self._load_data()
        return data.get(key)

    def set(self, key: str, value: str) -> None:
        """Set *key* to *value*, persisting to disk (no size guard)."""
        data = self._load_data()
        data[key] = value
        # Atomic write without enforcing size limit
        tmp_path = self.path.parent / (self.path.name + ".tmp")
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        with open(tmp_path, "wb") as tmp_file:
            tmp_file.write(content)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, self.path)

    def append(self, key: str, value: str) -> None:
        """Append *value* to existing key, separated by a newline marker."""
        data = self._load_data()
        existing = data.get(key, "")
        if existing:
            new_value = f"{existing}\n---\n{value}"
        else:
            new_value = value
        data[key] = new_value
        self._write_data(data) 