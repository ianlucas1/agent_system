import os
import json
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

WORKSPACE_DIRS = [
    ".agent_workspace",  # This path is relative to project root, ensure bootstrap is run from project root
    "logs",
    "inbox",
    "exec_requests",
    "data",
]


def ensure_dirs():
    logger.info("Ensuring workspace directories exist...")
    for d in WORKSPACE_DIRS:
        try:
            # If bootstrap.py is in src/, WORKSPACE_DIRS should ideally be relative to PROJECT_ROOT.
            # For .agent_workspace to be at project root, path should be os.path.join(config.PROJECT_ROOT_DIR, d)
            # However, bootstrap_agent.py was in root, so WORKSPACE_DIRS were relative to root.
            # Let's assume this script is run from project root for now.
            os.makedirs(d, exist_ok=True)
            logger.debug(f"Directory {d} ensured.")
        except Exception as e:
            logger.error(f"Could not create directory {d}: {e}", exc_info=True)
            # Decide if this is a fatal error for bootstrap


def write_session_bootstrap():
    logger.info("Writing session bootstrap file...")
    state = {
        "status": "initialized",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "next_task": "toolchain_discovery",
    }
    # Assuming .agent_workspace is at project root where this script is expected to be run from.
    path = os.path.join(".agent_workspace", "session_bootstrap.json")
    try:
        with open(path, "w") as f:
            json.dump(state, f, indent=2)
        logger.info(f"Session bootstrap file written to {path}")
    except Exception as e:
        logger.error(
            f"Could not write session bootstrap file to {path}: {e}", exc_info=True
        )


def main():
    ensure_dirs()
    write_session_bootstrap()
    logger.info("Bootstrap complete ✓")


if __name__ == "__main__":
    # If this script is run directly, ensure the current working directory is the project root
    # or adjust paths in WORKSPACE_DIRS and for session_bootstrap.json accordingly.
    # For now, assumes it's run from project root.
    main()
