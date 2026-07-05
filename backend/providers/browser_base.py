"""
Base Browser AI Provider for MetaPilot AI

Defines the interface for AI providers that use browser automation.
"""

import logging
from abc import abstractmethod
from typing import Optional, Dict, Any, List, AsyncGenerator

from .base import AIProvider, ProviderConfig, ProviderResponse, ChatResponse, ChatMessage
from ..browser.browser_manager import browser_manager

logger = logging.getLogger(__name__)


class BrowserAIProvider(AIProvider):
    """
    Abstract base class for browser-based AI providers.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config)
        self.browser_manager = browser_manager

    @abstractmethod
    async def login(self) -> bool:
        """Log in to the service if needed."""
        pass

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Generate text using browser automation.
        """
        conversation_id = kwargs.get("conversation_id")

        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.append({"role": "user", "content": prompt})

        response = await self.chat(chat_messages, model=model, **kwargs)

        return ProviderResponse(
            text=response.text,
            model=response.model,
            provider=self.name,
            finish_reason=response.finish_reason,
            metadata=response.metadata
        )

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> ChatResponse:
        """
        Generate a chat response using browser automation.
        """
        pass

    async def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        response = await self.generate(prompt, model, system_prompt, **kwargs)
        yield response.text
