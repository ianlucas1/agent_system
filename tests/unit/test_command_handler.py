import os
import sys
import pytest

# Add the project root to sys.path for src-based imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.handlers.command import CommandHandler, CommandType
from src.tools.file_system import FileManagerTool

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