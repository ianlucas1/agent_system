import pytest
from src.tools.memory import MemoryTool
from src.tools.base import ToolInput


class DummyBus:
    def __init__(self):
        self.storage = {}

    def get(self, key):
        return self.storage.get(key)

    def set(self, key, value):
        self.storage[key] = value

    def append(self, key, value):
        prev = self.storage.get(key, "")
        if prev:
            self.storage[key] = f"{prev}\n---\n{value}"
        else:
            self.storage[key] = value


@ pytest.fixture
def bus():
    return DummyBus()


@ pytest.fixture
def tool(bus):
    return MemoryTool(bus=bus)


def test_get_existing(tool, bus):
    bus.storage['a'] = '1'
    result = tool.execute(ToolInput("get", {"key": 'a'}))
    assert result.success
    assert result.data['value'] == '1'
    assert result.message == '1'


def test_get_missing(tool):
    result = tool.execute(ToolInput("get", {"key": 'b'}))
    assert result.success
    assert result.data['value'] is None
    assert result.message == ''


def test_set(tool, bus):
    result = tool.execute(ToolInput("set", {"key": 'x', "value": 'y'}))
    assert result.success
    assert bus.storage['x'] == 'y'
    assert result.data['value'] == 'y'
    assert result.message == 'y'


def test_append(tool, bus):
    bus.storage['a'] = 'foo'
    result = tool.execute(ToolInput("append", {"key": 'a', "value": 'bar'}))
    expected = 'foo\n---\nbar'
    assert result.success
    assert bus.storage['a'] == expected
    assert result.data['value'] == expected
    assert result.message == expected


def test_unsupported_op(tool):
    result = tool.execute(ToolInput("delete", {"key": 'a'}))
    assert not result.success
    assert "Unsupported MemoryTool operation" in result.error


def test_missing_key(tool):
    result = tool.execute(ToolInput("get", {}))
    assert not result.success
    assert "key" in result.error


def test_missing_value_for_set(tool):
    result = tool.execute(ToolInput("set", {"key": 'a'}))
    assert not result.success
    assert "value" in result.error


def test_missing_value_for_append(tool):
    result = tool.execute(ToolInput("append", {"key": 'a'}))
    assert not result.success
    assert "value" in result.error 