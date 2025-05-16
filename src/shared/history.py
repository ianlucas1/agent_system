import json
import pathlib
HIST_PATH = pathlib.Path("agent_workspace/chat_history.json")

def load() -> list:
    if HIST_PATH.exists():
        return json.loads(HIST_PATH.read_text())
    return []

def append(role: str, content: str):
    convo = load()
    convo.append({"r": role, "c": content})
    HIST_PATH.parent.mkdir(exist_ok=True)
    HIST_PATH.write_text(json.dumps(convo, indent=0))

def reset():
    HIST_PATH.unlink(missing_ok=True) 