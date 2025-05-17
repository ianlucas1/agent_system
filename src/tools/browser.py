from .base import Tool, ToolInput, ToolOutput
from .registry import ToolRegistry

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import asyncio

logger = logging.getLogger(__name__)

class BrowserTool(Tool):
    def __init__(self):
        self._playwright_manager = async_playwright()
        self._playwright = None
        self._browser = None
        self._context = None
        self._started = False

    async def _ensure_started(self):
        if not self._started:
            self._playwright = await self._playwright_manager.start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._context = await self._browser.new_context()
            self._started = True

    async def open_url(self, url: str) -> str:
        await self._ensure_started()
        if not self._context: # Should be initialized by _ensure_started
            return "⚠️ Browser context not initialized."
        page = await self._context.new_page()
        try:
            await page.goto(url, timeout=10000)  # 10s timeout
            # Using page.evaluate to get innerText, as page.content() might be too much
            # and page.inner_text() is not available on the Page object directly in async.
            text = await page.evaluate("() => document.body.innerText")
            return text[:4000] if text else "" # Limit output for safety
        except PlaywrightTimeoutError:
            return "⏰ Timeout loading page."
        except Exception as e:
            logger.exception(f"Error browsing {url}")
            return f"⚠️ Error: {e}"
        finally:
            if page:
                await page.close()

    # EXECUTE IS NOW SYNCHRONOUS due to asyncio.run() workaround
    def execute(self, tool_input: ToolInput) -> ToolOutput:
        op = tool_input.operation_name.lower().strip()
        args = tool_input.args or {}
        if op == "browse":
            url = args.get("url")
            if not url or not isinstance(url, str):
                return ToolOutput(success=False, error="/browse requires a URL string.")
            # WORKAROUND: Use asyncio.run to call the async open_url from this sync-behaving execute method.
            # This is to accommodate the synchronous CommandHandler.execute_command.
            # A proper fix would involve making CommandHandler and its callers async.
            try:
                # Ensure there's an event loop or create one for asyncio.run()
                # This might conflict if an outer loop (e.g. from Streamlit/pytest-asyncio) is already running.
                result = asyncio.run(self.open_url(url))
            except RuntimeError as e:
                if "cannot be called from a running event loop" in str(e):
                    # If already in a loop, try to schedule and run differently (more complex, may not work here easily)
                    # For now, log and return error. This indicates the workaround isn't sufficient.
                    logger.error(f"asyncio.run failed in BrowserTool.execute due to existing loop: {e}")
                    return ToolOutput(success=False, error=f"Async execution error: {e}. BrowserTool may need full async integration.")
                raise # Re-raise other RuntimeErrors
            return ToolOutput(success=True, message=result)
        else:
            return ToolOutput(success=False, error=f"Unsupported operation: {op}")

    async def close(self): # New async close method
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright: # Check if playwright instance was obtained
            await self._playwright.stop() # Stop the playwright instance
            self._playwright = None
        self._started = False

# ToolRegistry registration remains synchronous as it's about object availability,
# not its execution. The execution itself is now async.
ToolRegistry.register("browser", BrowserTool()) 