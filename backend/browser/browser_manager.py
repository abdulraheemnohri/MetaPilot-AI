"""
Browser Manager for MetaPilot AI

Manages headless browser instances for web scraping and browsing.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    headless: bool = True
    width: int = 1920
    height: int = 1080
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MetaPilot-AI/1.0"
    timeout: int = 30000
    max_concurrent: int = 5


@dataclass
class PageResult:
    url: str
    title: str
    content: str
    html: str
    links: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class BrowserManager:
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._contexts: Dict[str, Any] = {}
        self._pages: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        try:
            from playwright.async_api import async_playwright
            self._playwright = async_playwright()
            self._browser = await self._playwright.chromium.launch(
                headless=self.config.headless,
                args=[f"--window-size={self.config.width},{self.config.height}", "--disable-gpu", "--no-sandbox"],
            )
            self._initialized = True
            logger.info("Browser manager initialized")
        except ImportError:
            logger.error("Playwright not installed. Install with: pip install playwright && playwright install")
            raise
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            raise

    async def shutdown(self):
        if not self._initialized:
            return
        try:
            for page_id, page in self._pages.items():
                try:
                    await page.close()
                except:
                    pass
            for context_id, context in self._contexts.items():
                try:
                    await context.close()
                except:
                    pass
            if self._browser:
                await self._browser.close()
            if hasattr(self, '_playwright'):
                await self._playwright.stop()
            self._initialized = False
            logger.info("Browser manager shutdown")
        except Exception as e:
            logger.error(f"Error shutting down browser: {e}")

    @asynccontextmanager
    async def get_page(self, context_id: str = "default"):
        if not self._initialized:
            await self.initialize()
        if context_id not in self._contexts:
            self._contexts[context_id] = await self._browser.new_context(
                viewport={"width": self.config.width, "height": self.config.height},
                user_agent=self.config.user_agent,
            )
        context = self._contexts[context_id]
        page = await context.new_page()
        page_id = f"{context_id}-{len(self._pages)}"
        self._pages[page_id] = page
        try:
            yield page
        finally:
            try:
                await page.close()
            except:
                pass
            if page_id in self._pages:
                del self._pages[page_id]

    async def browse(self, url: str, wait_until: str = "domcontentloaded") -> PageResult:
        if not self._initialized:
            await self.initialize()
        async with self.get_page() as page:
            try:
                await page.goto(url, wait_until=wait_until, timeout=self.config.timeout)
                title = await page.title()
                html = await page.content()
                content = await page.evaluate("() => document.body.innerText")
                links = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href).filter(href => href && href.startsWith('http'))")
                metadata = {"url": url, "title": title, "language": await page.evaluate("() => document.documentElement.lang"), "content_length": len(content), "html_length": len(html), "link_count": len(links)}
                return PageResult(url=url, title=title, content=content, html=html, links=links, metadata=metadata)
            except Exception as e:
                logger.error(f"Error browsing {url}: {e}")
                raise

    async def screenshot(self, url: str, path: str, full_page: bool = False) -> str:
        if not self._initialized:
            await self.initialize()
        async with self.get_page() as page:
            await page.goto(url, wait_until="networkidle", timeout=self.config.timeout)
            await page.screenshot(path=path, full_page=full_page)
            return path

    async def extract_text(self, url: str) -> str:
        result = await self.browse(url)
        return result.content

    async def extract_links(self, url: str) -> List[str]:
        result = await self.browse(url)
        return result.links


browser_manager = BrowserManager()