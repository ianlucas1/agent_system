import pytest
import shutil
import os
from src.tools.memory import ChromaMemoryTool
from src.tools.base import ToolInput

CHROMA_PATH = os.path.join("agent_workspace", "chroma_db")

@pytest.fixture(autouse=True)
def cleanup_chroma():
    # Remove Chroma DB before and after each test for isolation
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    yield
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

def test_remember_and_recall():
    tool = ChromaMemoryTool()
    text = "The Eiffel Tower is in Paris."
    # Remember a fact
    result = tool.execute(ToolInput("remember", {"text": text}))
    assert result.success
    assert "Remembered" in result.message
    # Recall with a related query
    recall = tool.execute(ToolInput("recall", {"query": "Where is the Eiffel Tower?"}))
    assert recall.success
    assert "Eiffel Tower" in recall.message

def test_recall_no_match():
    tool = ChromaMemoryTool()
    # Add a fact
    tool.execute(ToolInput("remember", {"text": "The Eiffel Tower is in Paris."}))
    # Query with something unrelated
    recall = tool.execute(ToolInput("recall", {"query": "Completely unrelated query"}))
    assert recall.success
    # NOTE: Chroma always returns the closest match, even for unrelated queries.
    # This test only checks that the tool does not error.

def test_remember_requires_text():
    tool = ChromaMemoryTool()
    result = tool.execute(ToolInput("remember", {}))
    assert not result.success
    assert "/remember requires a text string" in result.error

def test_recall_requires_query():
    tool = ChromaMemoryTool()
    result = tool.execute(ToolInput("recall", {}))
    assert not result.success
    assert "/recall requires a query string" in result.error 