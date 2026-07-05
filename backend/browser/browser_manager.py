"""
Browser Manager for MetaPilot AI

Manages headless browser instances with session persistence and conversation pinning.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    headless: bool = True
    width: int = 1920
    height: int = 1080
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MetaPilot-AI/1.0"
    timeout: int = 30000
    max_concurrent: int = 5
    user_data_dir: str = "./cache/browser"


class BrowserManager:
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._playwright = None
        self._initialized = False
        self._pages = {}
        self._conversation_pages = {} # conversation_id -> page

        # Ensure cache dir exists
        Path(self.config.user_data_dir).mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        if self._initialized:
            return
        try:
            from playwright.async_api import async_playwright
            self._playwright_context_manager = async_playwright()
            self._playwright = await self._playwright_context_manager.start()

            # Use launch_persistent_context for session reuse
            self._browser_context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=self.config.user_data_dir,
                headless=self.config.headless,
                viewport={"width": self.config.width, "height": self.config.height},
                user_agent=self.config.user_agent,
                args=["--disable-gpu", "--no-sandbox"]
            )

            self._initialized = True
            logger.info(f"Browser manager initialized with persistent context in {self.config.user_data_dir}")
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            raise

    async def shutdown(self):
        if not self._initialized:
            return
        try:
            for page in self._conversation_pages.values():
                try: await page.close()
                except: pass
            if hasattr(self, '_browser_context'):
                await self._browser_context.close()
            if self._playwright:
                await self._playwright_context_manager.__aexit__()
            self._initialized = False
            logger.info("Browser manager shutdown")
        except Exception as e:
            logger.error(f"Error shutting down browser: {e}")

    @asynccontextmanager
    async def get_page(self, conversation_id: Optional[str] = None):
        if not self._initialized:
            await self.initialize()

        if conversation_id and conversation_id in self._conversation_pages:
            page = self._conversation_pages[conversation_id]
            if not page.is_closed():
                yield page
                return

        page = await self._browser_context.new_page()
        if conversation_id:
            self._conversation_pages[conversation_id] = page

        page_id = f"{conversation_id or 'default'}-{id(page)}"
        self._pages[page_id] = page
        try:
            yield page
        finally:
            if not conversation_id:
                try:
                    await page.close()
                except:
                    pass
                if page_id in self._pages:
                    del self._pages[page_id]

    async def close_conversation(self, conversation_id: str):
        if conversation_id in self._conversation_pages:
            page = self._conversation_pages[conversation_id]
            try: await page.close()
            except: pass
            del self._conversation_pages[conversation_id]

browser_manager = BrowserManager()
