"""
You.com Browser Provider for MetaPilot AI
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List

from .base import ProviderType, ChatResponse, ChatMessage
from .browser_base import BrowserAIProvider

logger = logging.getLogger(__name__)

class YouBrowserProvider(BrowserAIProvider):
    provider_type = ProviderType.LOCAL
    name = "You.com (Browser)"

    def __init__(self, config: Optional[Any] = None):
        super().__init__(config)
        self.url = "https://you.com"

    async def login(self) -> bool:
        async with self.browser_manager.get_page(conversation_id="login") as page:
            await page.goto(self.url)
            try:
                await page.wait_for_selector("textarea", timeout=5000)
                return True
            except: return False

    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> ChatResponse:
        last_message = messages[-1]["content"]
        async with self.browser_manager.get_page(conversation_id=kwargs.get("conversation_id")) as page:
            await page.goto(self.url)
            await page.fill("textarea", last_message)
            await page.press("textarea", "Enter")
            await asyncio.sleep(8)
            responses = await page.query_selector_all(".chat-message")
            text = await responses[-1].evaluate("el => el.innerText") if responses else "Error extraction"
            return ChatResponse(text=text, model=model or "you-browser", provider=self.name, message=ChatMessage(role="assistant", content=text))
