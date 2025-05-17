from __future__ import annotations


from playwright.sync_api import sync_playwright

from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry


class BrowserTool(Tool):
    """Simple tool to fetch page text using Playwright."""

    def open_url(self, url: str) -> str:
        """Open *url* and return the page body text."""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            content = page.inner_text("body")
            browser.close()
            return content

    def execute(self, tool_input: ToolInput) -> ToolOutput:  # noqa: D401
        op = tool_input.operation_name.lower().strip()
        if op not in {"open", "visit", "fetch"}:
            return ToolOutput(success=False, error=f"Unsupported operation: {op}")
        url = tool_input.args.get("url") if tool_input.args else None
        if not url or not isinstance(url, str):
            return ToolOutput(success=False, error="No URL provided.")
        try:
            text = self.open_url(url)
        except Exception as exc:  # noqa: BLE001
            return ToolOutput(success=False, error=str(exc))
        return ToolOutput(success=True, message=text)


# Register globally
ToolRegistry.register("browser", BrowserTool())
