# MetaPilot AI - Browser Provider Integration Guide

This guide explains how to add new browser-based AI providers using Playwright.

## 🏗️ Architecture

Browser providers inherit from `BrowserAIProvider` in `backend/providers/browser_base.py`. They use the global `browser_manager` to get a persistent or temporary page.

## 📝 Integration Steps

### 1. Create the provider file
E.g., `backend/providers/my_new_ai_browser.py`.

### 2. Implement the class
```python
class MyNewAIBrowserProvider(BrowserAIProvider):
    name = "My New AI"
    def __init__(self, config=None):
        super().__init__(config)
        self.url = "https://mynewai.com"

    async def login(self):
        # Implementation to check or perform login
        return True

    async def chat(self, messages, model=None, **kwargs):
        # Implementation using self.browser_manager.get_page()
        # 1. Goto self.url
        # 2. Fill input selector with messages[-1]["content"]
        # 3. Press Enter
        # 4. Wait for output selector
        # 5. Return ChatResponse
```

### 3. Register the provider
Add it to `backend/providers/registry.py` inside the `initialize` method.

### 4. Define capabilities
Update `backend/providers/capabilities.py` to include the new provider's strengths (e.g., `Capability.CODE`).

## 🛠️ Selectors & Shadow DOM
Some AI sites use Shadow DOM. Use `page.evaluate` to extract content if standard selectors fail.
