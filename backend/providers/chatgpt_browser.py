"""
ChatGPT Browser Provider for MetaPilot AI

Implementation of AIProvider for ChatGPT via browser automation.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List

from .base import ProviderType, ChatResponse, ChatMessage
from .browser_base import BrowserAIProvider

logger = logging.getLogger(__name__)


class ChatGPTBrowserProvider(BrowserAIProvider):
    """
    ChatGPT browser-based provider.
    """

    provider_type = ProviderType.LOCAL  # Using LOCAL as placeholder for browser-based
    name = "ChatGPT (Browser)"

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.url = "https://chat.openai.com"

    async def login(self) -> bool:
        """
        User-authorized login session reuse.
        """
        async with self.browser_manager.get_page() as page:
            await page.goto(self.url)
            # Check if logged in
            try:
                await page.wait_for_selector("textarea", timeout=5000)
                return True
            except:
                logger.warning("ChatGPT not logged in or taking too long to load")
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
            await page.fill("textarea", last_message)
            await page.press("textarea", "Enter")

            # Wait for response (simplified)
            await asyncio.sleep(5)

            # Extract last response
            responses = await page.query_selector_all(".markdown")
            if responses:
                text = await responses[-1].inner_text()
            else:
                text = "Error: Could not extract response"

            return ChatResponse(
                text=text,
                model=model or "chatgpt-browser",
                provider=self.name,
                message=ChatMessage(role="assistant", content=text)
            )
