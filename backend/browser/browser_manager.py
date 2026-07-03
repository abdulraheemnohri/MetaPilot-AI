"""
MetaPilot AI - Browser Manager

Manages browser instances for web automation and scraping.
"""

import logging
import asyncio
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
import time

logger = logging.getLogger(__name__)


class BrowserType(Enum):
    """Types of browsers supported."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserContextType(Enum):
    """Types of browser contexts."""
    DEFAULT = "default"
    INCognito = "incognito"
    PERSISTENT = "persistent"


@dataclass
class BrowserConfig:
    """Configuration for a browser instance."""
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    slow_mo: int = 0  # Slow down operations by this many milliseconds
    timeout: int = 30000  # Default timeout in milliseconds
    viewport: Optional[Tuple[int, int]] = None
    user_agent: Optional[str] = None
    proxy: Optional[Dict[str, str]] = None
    download_path: Optional[str] = None
    video_size: Optional[Tuple[int, int]] = None
    device_scale_factor: Optional[float] = None
    locale: Optional[str] = None
    timezone_id: Optional[str] = None
    geolocation: Optional[Dict[str, float]] = None
    permissions: Optional[List[str]] = None
    extra_args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "browser_type": self.browser_type.value,
            "headless": self.headless,
            "slow_mo": self.slow_mo,
            "timeout": self.timeout,
            "viewport": self.viewport,
            "user_agent": self.user_agent,
            "proxy": self.proxy,
            "download_path": self.download_path,
            "video_size": self.video_size,
            "device_scale_factor": self.device_scale_factor,
            "locale": self.locale,
            "timezone_id": self.timezone_id,
            "geolocation": self.geolocation,
            "permissions": self.permissions,
            "extra_args": self.extra_args,
            "env": self.env
        }


@dataclass
class BrowserInstance:
    """Represents a browser instance."""
    instance_id: str
    browser_type: BrowserType
    config: BrowserConfig
    is_connected: bool = False
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "browser_type": self.browser_type.value,
            "config": self.config.to_dict(),
            "is_connected": self.is_connected,
            "created_at": self.created_at,
            "last_used": self.last_used
        }


class BrowserManager:
    """
    Manages browser instances for web automation.
    
    Supports Playwright for browser automation.
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        """
        Initialize the browser manager.
        
        Args:
            config: Default browser configuration
        """
        self.config = config or BrowserConfig()
        self._browsers: Dict[str, Any] = {}
        self._instances: Dict[str, BrowserInstance] = {}
        self._lock = asyncio.Lock()
        self._temp_dir = tempfile.mkdtemp(prefix="metapilot_browser_")
        
        # Ensure temp directory exists
        Path(self._temp_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info("Browser manager initialized")
    
    async def create_browser(self, 
                           config: Optional[BrowserConfig] = None,
                           instance_id: Optional[str] = None) -> BrowserInstance:
        """
        Create a new browser instance.
        
        Args:
            config: Browser configuration (uses default if not provided)
            instance_id: Optional instance ID
        
        Returns:
            BrowserInstance object
        """
        import uuid
        
        async with self._lock:
            # Generate instance ID if not provided
            if instance_id is None:
                instance_id = str(uuid.uuid4())
            
            # Use provided config or default
            browser_config = config or self.config
            
            try:
                # Import playwright
                from playwright.async_api import async_playwright
                
                # Launch browser
                playwright = await async_playwright().start()
                
                launch_options = {
                    "headless": browser_config.headless,
                    "slow_mo": browser_config.slow_mo,
                    "timeout": browser_config.timeout,
                }
                
                # Add browser-specific options
                if browser_config.browser_type == BrowserType.CHROMIUM:
                    browser = await playwright.chromium.launch(**launch_options)
                elif browser_config.browser_type == BrowserType.FIREFOX:
                    browser = await playwright.firefox.launch(**launch_options)
                elif browser_config.browser_type == BrowserType.WEBKIT:
                    browser = await playwright.webkit.launch(**launch_options)
                else:
                    browser = await playwright.chromium.launch(**launch_options)
                
                # Store browser
                self._browsers[instance_id] = {
                    "playwright": playwright,
                    "browser": browser,
                    "config": browser_config
                }
                
                # Create instance
                instance = BrowserInstance(
                    instance_id=instance_id,
                    browser_type=browser_config.browser_type,
                    config=browser_config,
                    is_connected=True
                )
                
                self._instances[instance_id] = instance
                
                logger.info(f"Created browser instance: {instance_id}")
                return instance
                
            except ImportError:
                logger.error("Playwright not installed. Install with: pip install playwright")
                raise
            except Exception as e:
                logger.error(f"Error creating browser: {e}")
                raise
    
    async def get_browser(self, instance_id: str) -> Any:
        """
        Get a browser instance by ID.
        
        Args:
            instance_id: Browser instance ID
        
        Returns:
            Browser object (Playwright browser)
        """
        async with self._lock:
            if instance_id not in self._browsers:
                raise ValueError(f"Browser instance {instance_id} not found")
            
            # Update last used time
            if instance_id in self._instances:
                self._instances[instance_id].last_used = time.time()
            
            return self._browsers[instance_id]["browser"]
    
    async def create_context(self, 
                            instance_id: str,
                            context_type: BrowserContextType = BrowserContextType.DEFAULT,
                            **kwargs) -> Any:
        """
        Create a new browser context.
        
        Args:
            instance_id: Browser instance ID
            context_type: Type of context
            **kwargs: Additional context options
        
        Returns:
            Browser context
        """
        browser = await self.get_browser(instance_id)
        
        context_options = {}
        
        # Add viewport if specified in config
        browser_info = self._browsers.get(instance_id)
        if browser_info and browser_info["config"].viewport:
            context_options["viewport"] = {
                "width": browser_info["config"].viewport[0],
                "height": browser_info["config"].viewport[1]
            }
        
        # Add user agent
        if browser_info and browser_info["config"].user_agent:
            context_options["user_agent"] = browser_info["config"].user_agent
        
        # Add proxy
        if browser_info and browser_info["config"].proxy:
            context_options["proxy"] = browser_info["config"].proxy
        
        # Add geolocation
        if browser_info and browser_info["config"].geolocation:
            context_options["geolocation"] = browser_info["config"].geolocation
        
        # Add permissions
        if browser_info and browser_info["config"].permissions:
            context_options["permissions"] = browser_info["config"].permissions
        
        # Add locale
        if browser_info and browser_info["config"].locale:
            context_options["locale"] = browser_info["config"].locale
        
        # Add timezone
        if browser_info and browser_info["config"].timezone_id:
            context_options["timezone_id"] = browser_info["config"].timezone_id
        
        # Merge with kwargs
        context_options.update(kwargs)
        
        context = await browser.new_context(**context_options)
        
        # Set default timeout
        context.set_default_timeout(browser_info["config"].timeout)
        
        return context
    
    async def create_page(self, 
                         instance_id: str,
                         context: Optional[Any] = None,
                         **kwargs) -> Any:
        """
        Create a new browser page.
        
        Args:
            instance_id: Browser instance ID
            context: Optional browser context (creates new if not provided)
            **kwargs: Additional page options
        
        Returns:
            Browser page
        """
        browser = await self.get_browser(instance_id)
        
        if context is None:
            context = await self.create_context(instance_id)
        
        page = await context.new_page(**kwargs)
        
        # Set viewport if not already set
        if not kwargs.get("viewport"):
            browser_info = self._browsers.get(instance_id)
            if browser_info and browser_info["config"].viewport:
                await page.set_viewport_size({
                    "width": browser_info["config"].viewport[0],
                    "height": browser_info["config"].viewport[1]
                })
        
        return page
    
    async def navigate(self, 
                      instance_id: str,
                      url: str,
                      context: Optional[Any] = None,
                      wait_until: str = "domcontentloaded",
                      timeout: Optional[int] = None) -> Any:
        """
        Navigate to a URL in a new or existing page.
        
        Args:
            instance_id: Browser instance ID
            url: URL to navigate to
            context: Optional browser context
            wait_until: Wait until this event (load, domcontentloaded, networkidle)
            timeout: Optional timeout in milliseconds
        
        Returns:
            Browser page
        """
        page = await self.create_page(instance_id, context)
        
        timeout = timeout or self._browsers.get(instance_id, {}).get("config", {}).timeout
        
        await page.goto(url, wait_until=wait_until, timeout=timeout)
        
        return page
    
    async def take_screenshot(self, 
                            instance_id: str,
                            path: Optional[str] = None,
                            full_page: bool = False,
                            **kwargs) -> bytes:
        """
        Take a screenshot.
        
        Args:
            instance_id: Browser instance ID
            path: Optional path to save screenshot
            full_page: Whether to capture full page
            **kwargs: Additional screenshot options
        
        Returns:
            Screenshot as bytes
        """
        page = await self.create_page(instance_id)
        
        screenshot_bytes = await page.screenshot(path=path, full_page=full_page, **kwargs)
        
        return screenshot_bytes
    
    async def get_page_content(self, 
                               instance_id: str,
                               url: str,
                               wait_until: str = "domcontentloaded",
                               timeout: Optional[int] = None) -> str:
        """
        Get the content of a web page.
        
        Args:
            instance_id: Browser instance ID
            url: URL to fetch
            wait_until: Wait until this event
            timeout: Optional timeout in milliseconds
        
        Returns:
            Page content as HTML
        """
        page = await self.navigate(instance_id, url, wait_until=wait_until, timeout=timeout)
        
        content = await page.content()
        
        await page.close()
        
        return content
    
    async def extract_text(self, 
                          instance_id: str,
                          url: str,
                          selector: Optional[str] = None,
                          wait_until: str = "domcontentloaded") -> str:
        """
        Extract text from a web page.
        
        Args:
            instance_id: Browser instance ID
            url: URL to fetch
            selector: Optional CSS selector to extract text from
            wait_until: Wait until this event
        
        Returns:
            Extracted text
        """
        page = await self.navigate(instance_id, url, wait_until=wait_until)
        
        if selector:
            element = await page.query_selector(selector)
            if element:
                text = await element.inner_text()
            else:
                text = await page.evaluate("() => document.body.innerText")
        else:
            text = await page.evaluate("() => document.body.innerText")
        
        await page.close()
        
        return text
    
    async def fill_form(self, 
                       instance_id: str,
                       url: str,
                       form_data: Dict[str, str],
                       submit: bool = True,
                       wait_until: str = "domcontentloaded") -> Optional[str]:
        """
        Fill and submit a form.
        
        Args:
            instance_id: Browser instance ID
            url: URL of the page with the form
            form_data: Dictionary of field names to values
            submit: Whether to submit the form
            wait_until: Wait until this event
        
        Returns:
            Result page URL if form was submitted, None otherwise
        """
        page = await self.navigate(instance_id, url, wait_until=wait_until)
        
        # Fill form fields
        for field_name, value in form_data.items():
            try:
                # Try different input types
                input_element = await page.query_selector(f'input[name="{field_name}"]')
                if input_element:
                    await input_element.fill(value)
                else:
                    textarea_element = await page.query_selector(f'textarea[name="{field_name}"]')
                    if textarea_element:
                        await textarea_element.fill(value)
                    else:
                        # Try by ID
                        input_element = await page.query_selector(f'#{field_name}')
                        if input_element:
                            await input_element.fill(value)
            except Exception as e:
                logger.warning(f"Could not fill field {field_name}: {e}")
        
        if submit:
            # Find and click submit button
            submit_button = await page.query_selector('button[type="submit"]')
            if submit_button:
                await submit_button.click()
            else:
                submit_input = await page.query_selector('input[type="submit"]')
                if submit_input:
                    await submit_input.click()
            
            # Wait for navigation
            await page.wait_for_load_state("domcontentloaded")
            
            result_url = page.url
            await page.close()
            return result_url
        
        await page.close()
        return None
    
    async def close_browser(self, instance_id: str) -> bool:
        """
        Close a browser instance.
        
        Args:
            instance_id: Browser instance ID
        
        Returns:
            True if closed successfully
        """
        async with self._lock:
            if instance_id not in self._browsers:
                return False
            
            try:
                browser_info = self._browsers[instance_id]
                
                # Close all contexts
                contexts = browser_info["browser"].contexts
                for context in contexts:
                    await context.close()
                
                # Close browser
                await browser_info["browser"].close()
                
                # Close playwright
                await browser_info["playwright"].stop()
                
                # Remove from tracking
                del self._browsers[instance_id]
                if instance_id in self._instances:
                    self._instances[instance_id].is_connected = False
                
                logger.info(f"Closed browser instance: {instance_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error closing browser {instance_id}: {e}")
                return False
    
    async def close_all(self) -> int:
        """
        Close all browser instances.
        
        Returns:
            Number of instances closed
        """
        async with self._lock:
            instance_ids = list(self._browsers.keys())
            count = 0
            
            for instance_id in instance_ids:
                if await self.close_browser(instance_id):
                    count += 1
            
            logger.info(f"Closed {count} browser instances")
            return count
    
    async def list_instances(self) -> List[BrowserInstance]:
        """
        List all browser instances.
        
        Returns:
            List of BrowserInstance objects
        """
        async with self._lock:
            return list(self._instances.values())
    
    async def get_instance(self, instance_id: str) -> Optional[BrowserInstance]:
        """
        Get a browser instance by ID.
        
        Args:
            instance_id: Browser instance ID
        
        Returns:
            BrowserInstance or None if not found
        """
        async with self._lock:
            return self._instances.get(instance_id)
    
    async def cleanup(self) -> None:
        """Clean up all resources."""
        await self.close_all()
        
        # Clean up temp directory
        try:
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {e}")


# Global browser manager instance
browser_manager = None


def get_browser_manager(config: Optional[BrowserConfig] = None) -> BrowserManager:
    """Get or create the global browser manager."""
    global browser_manager
    if browser_manager is None:
        browser_manager = BrowserManager(config)
    return browser_manager
