"""shared.workspace

Provides temporary workspace directories for agents, with automatic cleanup.
"""
from contextlib import contextmanager
from pathlib import Path
import shutil
import os
from uuid import uuid4
from typing import Generator

class WorkspaceManager:
    """Manages temporary directories for agent workspaces."""

    BASE_DIR = Path(os.getcwd()) / "agent_workspace" / "tmp"

    @classmethod
    @contextmanager
    def temp_dir(cls, agent_name: str) -> Generator[Path, None, None]:
        """Create a temporary directory for *agent_name* and clean up after use."""
        agent_dir = cls.BASE_DIR / agent_name
        temp_path = agent_dir / str(uuid4())
        temp_path.mkdir(parents=True, exist_ok=True)
        try:
            yield temp_path
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)

    @classmethod
    def get_temp_dir(cls, agent_name: str) -> Path:
        """Return a new temporary directory path without context manager cleanup."""
        agent_dir = cls.BASE_DIR / agent_name
        temp_path = agent_dir / str(uuid4())
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path 