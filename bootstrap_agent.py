import os
import json
from datetime import datetime, timezone

WORKSPACE_DIRS = [
    ".agent_workspace",
    "logs",
    "inbox",
    "exec_requests",
    "data"
]

def ensure_dirs():
    for d in WORKSPACE_DIRS:
        os.makedirs(d, exist_ok=True)

def write_session_bootstrap():
    state = {
        "status": "initialized",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "next_task": "toolchain_discovery"
    }
    path = os.path.join(".agent_workspace", "session_bootstrap.json")
    with open(path, "w") as f:
        json.dump(state, f, indent=2)

def main():
    ensure_dirs()
    write_session_bootstrap()
    print("Bootstrap complete ✓")

if __name__ == "__main__":
    main() 