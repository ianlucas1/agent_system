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
    assert result.success
    # Verify bus storage
    assert dummy_bus.get(f"{context_key}.plan") == "PLAN"
    assert dummy_bus.get(f"{context_key}.code") == "CODE"
    assert dummy_bus.get(f"{context_key}.review") == "REVIEW"
    # Verify markdown output
    md = result.message
    assert "## Plan" in md and "PLAN" in md
    assert "## Code" in md and "CODE" in md
    assert "## Review" in md and "REVIEW" in md


def test_workflow_tool_implicit_key(dummy_bus, stub_multi):
    tool = WorkflowTool(bus=dummy_bus, multi_agent=stub_multi)
    task = "Simple Task"
    result = tool.execute(ToolInput("run", {"task": task}))
    assert result.success
    # Slugify produces 'simple_task'
    key = tool._slugify(task)
    assert dummy_bus.get(f"{key}.plan") == "PLAN"
    assert dummy_bus.get(f"{key}.code") == "CODE"
    assert dummy_bus.get(f"{key}.review") == "REVIEW"
    # ensure temp_dirs recorded and are unique per agent step
    assert hasattr(stub_multi, 'temp_dirs')
    assert len(stub_multi.temp_dirs) == 3
    assert len(set(stub_multi.temp_dirs)) == 3 