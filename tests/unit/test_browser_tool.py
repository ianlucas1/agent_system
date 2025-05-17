import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.tools.browser import BrowserTool
from src.tools.base import ToolInput


def test_open_local_file(tmp_path):
    html = tmp_path / "index.html"
    html.write_text("<html><body><h1>Hello</h1></body></html>")

    tool = BrowserTool()
    result = tool.execute(ToolInput("open", {"url": html.as_uri()}))

    assert result.success
    assert "Hello" in result.message
