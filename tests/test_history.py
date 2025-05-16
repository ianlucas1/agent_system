import pytest
import pathlib

# Assuming the history module is at src/shared/history.py
# Adjust the import path if necessary
import src.shared.history as history

TEST_HIST_PATH = pathlib.Path("agent_workspace/test_chat_history.json")

# Use a different path for testing to avoid clashing with live history
history.HIST_PATH = TEST_HIST_PATH

@pytest.fixture(autouse=True)
def cleanup_history_file():
    """Fixture to ensure the history file is clean before and after each test."""
    history.reset()
    yield
    history.reset()

def test_history_append_and_load():
    """Tests that messages are correctly appended and loaded."""
    history.append("user", "Hello")
    history.append("agent", "Hi there!")

    loaded_history = history.load()

    assert isinstance(loaded_history, list)
    assert len(loaded_history) == 2
    assert loaded_history[0] == {"r": "user", "c": "Hello"}
    assert loaded_history[1] == {"r": "agent", "c": "Hi there!"}

def test_history_reset():
    """Tests that history reset clears the file."""
    history.append("user", "Message 1")
    history.append("agent", "Response 1")

    assert TEST_HIST_PATH.exists()
    assert len(history.load()) == 2

    history.reset()

    assert not TEST_HIST_PATH.exists()
    assert len(history.load()) == 0 # Loading after reset should return empty list

def test_load_nonexistent_history():
    """Tests loading history when the file doesn't exist."""
    # Ensure file does not exist
    history.reset()

    loaded_history = history.load()

    assert isinstance(loaded_history, list)
    assert len(loaded_history) == 0

def test_history_multiple_appends():
    """Tests appending multiple messages."""
    messages = [
        ("user", "First message"),
        ("agent", "First response"),
        ("user", "Second message"),
        ("agent", "Second response"),
    ]

    for role, content in messages:
        history.append(role, content)

    loaded_history = history.load()

    assert len(loaded_history) == len(messages)
    for i, (role, content) in enumerate(messages):
        assert loaded_history[i] == {"r": role, "c": content} 