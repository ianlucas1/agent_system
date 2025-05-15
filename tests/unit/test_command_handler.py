import os
import sys
import pytest

# Add the project root to sys.path for src-based imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.handlers.command import CommandHandler, CommandType
from src.tools.file_system import FileManagerTool
from src.tools.base import ToolOutput

@pytest.fixture
def handler():
    return CommandHandler(file_tool=FileManagerTool())

def test_parse_read_command(handler):
    cmd = handler.parse('/read foo.txt', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.READ
    assert cmd.args == 'foo.txt'

def test_parse_list_command(handler):
    cmd = handler.parse('/list logs', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.LIST
    assert cmd.args == 'logs'

def test_parse_write_command(handler):
    cmd = handler.parse('/write foo.txt hello', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.WRITE
    assert cmd.args == ('foo.txt', 'hello')

def test_parse_overwrite_command(handler):
    cmd = handler.parse('/overwrite foo.txt', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.OVERWRITE
    assert cmd.args == 'foo.txt'

def test_parse_unknown_command(handler):
    cmd = handler.parse('/foobar', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.UNKNOWN

def test_parse_nl_write(handler):
    cmd = handler.parse('save this to bar.txt', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.WRITE
    assert cmd.args == ('bar.txt', None)

def test_parse_nl_list(handler):
    cmd = handler.parse("what's in data", [])
    assert cmd is not None
    assert cmd.command_type == CommandType.LIST
    assert cmd.args == 'data'

def test_parse_nl_read(handler):
    cmd = handler.parse('read foo.txt', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.READ
    assert cmd.args == 'foo.txt'

def test_parse_missing_read(handler):
    cmd = handler.parse('/read', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.UNKNOWN
    assert 'Usage' in cmd.args 

def test_cli_run_success(monkeypatch):
    handler = CommandHandler(file_tool=FileManagerTool())

    # stub ShellCommandTool
    class StubShell:
        def execute(self, ti):
            return ToolOutput(success=True, message="```shell\nhello\n```")

    from src.tools import registry as reg
    monkeypatch.setattr(reg.ToolRegistry, "get", lambda key: StubShell() if "shell" in key else None)

    cmd = handler.parse("/run echo hello", [])
    assert cmd.command_type == CommandType.RUN
    resp = handler.execute_command(cmd, chat_session=None, current_user_input="/run echo hello")
    assert "hello" in resp


def test_cli_run_empty():
    handler = CommandHandler(file_tool=FileManagerTool())
    cmd = handler.parse("/run", [])
    assert cmd.command_type == CommandType.UNKNOWN


def test_agent_payload_error(monkeypatch):
    handler = CommandHandler(file_tool=FileManagerTool())
    cmd = handler.parse("/agent { bad json", [])
    resp = handler.execute_command(cmd, chat_session=None, current_user_input="/agent { bad json")
    assert "Syntax error" in resp


def test_agent_success(monkeypatch, tmp_path):
    handler = CommandHandler(file_tool=FileManagerTool())

    class StubAgent:
        def execute(self, ti):
            return ToolOutput(success=True, message="done", data={})
    from src.tools import registry as reg
    monkeypatch.setattr(reg.ToolRegistry, "get", lambda key: StubAgent() if key=="agent.multi" else None)

    payload = {"agent_name": "PlannerAgent", "role_prompt": "plan", "task": "write"}
    import json
    cmd_str = "/agent " + json.dumps(payload)
    cmd = handler.parse(cmd_str, [])
    resp = handler.execute_command(cmd, chat_session=None, current_user_input=cmd_str)
    assert resp.startswith("[PlannerAgent]") 

def test_parse_mem_get(handler):
    cmd = handler.parse('/mem get foo', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.MEMORY
    assert cmd.args == ('get', 'foo', None)

def test_parse_mem_set(handler):
    cmd = handler.parse('/mem set key = value', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.MEMORY
    assert cmd.args == ('set', 'key', 'value')

def test_parse_mem_append(handler):
    cmd = handler.parse('/mem append log = entry', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.MEMORY
    assert cmd.args == ('append', 'log', 'entry')

def test_parse_mem_bad(handler):
    cmd = handler.parse('/mem set foo', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.UNKNOWN
    assert 'Usage' in cmd.args 

def test_parse_workflow(handler):
    cmd = handler.parse('/workflow Build hello world', [])
    assert cmd is not None
    assert cmd.command_type == CommandType.WORKFLOW
    assert cmd.args == 'Build hello world'

def test_execute_workflow(monkeypatch):
    handler = CommandHandler(file_tool=FileManagerTool())
    # stub WorkflowTool
    from src.tools import registry as reg
    class StubWorkflow:
        def execute(self, ti):
            return ToolOutput(success=True, message="## Plan\nA\n\n## Code\nB\n\n## Review\nC")
    monkeypatch.setattr(reg.ToolRegistry, 'get', lambda key: StubWorkflow() if key=='workflow.pcr' else None)
    cmd = handler.parse('/workflow Test task', [])
    resp = handler.execute_command(cmd, chat_session=None, current_user_input='/workflow Test task')
    assert '## Plan' in resp and '## Code' in resp and '## Review' in resp 