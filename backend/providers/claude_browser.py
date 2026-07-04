"""
Claude Browser Provider for MetaPilot AI

Implementation of AIProvider for Claude via browser automation.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List

from .base import ProviderType, ChatResponse, ChatMessage
from .browser_base import BrowserAIProvider

logger = logging.getLogger(__name__)


class ClaudeBrowserProvider(BrowserAIProvider):
    """
    Claude browser-based provider.
    """

    provider_type = ProviderType.LOCAL
    name = "Claude (Browser)"

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.url = "https://claude.ai"

    async def login(self) -> bool:
        """
        User-authorized login session reuse.
        """
        async with self.browser_manager.get_page() as page:
            await page.goto(self.url)
            try:
                await page.wait_for_selector("div[contenteditable='true']", timeout=5000)
                return True
            except:
                return False

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> ChatResponse:
        """
        Send message via browser.
        """
        last_message = messages[-1]["content"]

        async with self.browser_manager.get_page() as page:
            await page.goto(self.url)

            # Type message
            await page.fill("div[contenteditable='true']", last_message)
            await page.press("div[contenteditable='true']", "Enter")

            # Wait for response
            await asyncio.sleep(5)

            # Extract response (simplified)
            responses = await page.query_selector_all(".font-claude-message")
            if responses:
                text = await responses[-1].inner_text()
            else:
                text = "Error: Could not extract response"

            return ChatResponse(
                text=text,
                model=model or "claude-browser",
                provider=self.name,
                message=ChatMessage(role="assistant", content=text)
            )
