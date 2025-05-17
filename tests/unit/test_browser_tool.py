import pytest
from src.tools.browser import BrowserTool
from src.tools.base import ToolInput
import asyncio # Required for async tests

@pytest.mark.slow
async def test_browser_tool_browse_example_com():
    tool = BrowserTool()
    try:
        # Ensure Playwright is started for the tool instance before execution
        # This would typically be handled by the application lifecycle or a fixture
        # For a direct unit test like this, we can call _ensure_started if needed,
        # or rely on execute to call it.
        # await tool._ensure_started() # Not strictly needed if execute calls it

        input_args = ToolInput(operation_name="browse", args={"url": "https://example.com"})
        output = await tool.execute(input_args) # Await the async execute
        assert output.success
        assert "Example Domain" in output.message
    finally:
        await tool.close() # Ensure cleanup 