import pytest
from src.tools.base import ToolInput, ToolOutput
from src.tools.workflow import WorkflowTool


class DummyBus:
    def __init__(self):
        self.storage = {}

    def set(self, key, value):
        self.storage[key] = value

    def get(self, key):
        return self.storage.get(key)

    def append(self, key, value):
        pass


class StubMultiAgent:
    def __init__(self):
        self.calls = []
        self.outputs = ["PLAN", "CODE", "REVIEW"]
        self.temp_dirs = []  # store temp dir values from env var

    def execute(self, tool_input: ToolInput) -> ToolOutput:
        # record temp workspace from environment
        import os
        self.temp_dirs.append(os.environ.get("WORKSPACE_TEMP"))
        idx = len(self.calls)
        self.calls.append(tool_input)
        # Return valid JSON for CoderAgent step
        if idx == 1:
            msg = '{"files": [["foo.py", "print(1)\\n"]]}'
        else:
            msg = self.outputs[idx]
        return ToolOutput(success=True, message=msg, data={"reply": msg})


@pytest.fixture
def dummy_bus():
    return DummyBus()


@pytest.fixture
def stub_multi():
    return StubMultiAgent()


def test_workflow_tool_with_explicit_key(dummy_bus, stub_multi):
    tool = WorkflowTool(bus=dummy_bus, multi_agent=stub_multi)
    task = "Build a REST endpoint"
    context_key = "workflow_test"
    result = tool.execute(ToolInput("run", {"task": task, "context_key": context_key}))
    assert not result.success
    assert "QA failed" in result.message
    assert "Show QA log" in result.message
    # Verify bus storage
    assert dummy_bus.get(f"{context_key}.plan") == "PLAN"
    assert dummy_bus.get(f"{context_key}.code") == '{"files": [["foo.py", "print(1)\\n"]]}'
    # Verify markdown output
    md = result.message
    assert "## Plan" in md and "PLAN" in md
    assert "## Code" in md and '{"files": [["foo.py", "print(1)\\n"]]}' in md
    assert "## Review" not in md


def test_workflow_tool_implicit_key(dummy_bus, stub_multi):
    tool = WorkflowTool(bus=dummy_bus, multi_agent=stub_multi)
    task = "Simple Task"
    result = tool.execute(ToolInput("run", {"task": task}))
    assert not result.success
    assert "QA failed" in result.message
    assert "Show QA log" in result.message
    # Slugify produces 'simple_task'
    key = tool._slugify(task)
    assert dummy_bus.get(f"{key}.plan") == "PLAN"
    assert dummy_bus.get(f"{key}.code") == '{"files": [["foo.py", "print(1)\\n"]]}'
    # ensure temp_dirs recorded and are unique per agent step
    assert hasattr(stub_multi, 'temp_dirs')
    assert len(stub_multi.temp_dirs) == 2  # Planner and Coder
    assert len(set(stub_multi.temp_dirs)) == 2 