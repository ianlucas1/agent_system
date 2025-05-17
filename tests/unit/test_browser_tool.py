import pytest
from src.tools.browser import BrowserTool
from src.tools.base import ToolInput
import asyncio

@pytest.mark.slow
async def test_browser_tool_browse_example_com():
    tool = BrowserTool()
    try:
        input_args = ToolInput(operation_name="browse", args={"url": "https://example.com"})
        # Execute is now synchronous again due to internal asyncio.run workaround
        output = tool.execute(input_args)
        assert output.success
        assert "Example Domain" in output.message
    finally:
        await tool.close() # close is still async 