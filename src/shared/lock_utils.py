"""shared.lock_utils

Provides file-based locking utilities for ContextBus.
"""
from contextlib import contextmanager
from pathlib import Path
from filelock import FileLock, Timeout

class ContextBusLockTimeout(Exception):
    """Raised when acquiring a file lock times out."""
    pass

@contextmanager
def file_lock(path: Path | str, timeout: float = 3.0):
    """Context manager for a file lock associated with *path*."""
    p = Path(path)
    # Lock file has same name with '.lock' suffix
    lock_file = p.with_suffix(p.suffix + ".lock")
    lock = FileLock(str(lock_file), timeout=timeout)
    try:
        with lock:
            yield
    except Timeout:
        raise ContextBusLockTimeout(
            f"Could not acquire lock for {path} within {timeout} seconds"
        ) 