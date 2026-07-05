# MetaPilot AI - Plugin Development Guide

Plugins allow you to extend MetaPilot AI with custom tools, local commands, or specialized API connectors.

## 🏗️ Plugin Architecture

Every plugin must inherit from the `MetaPilotPlugin` base class located in `backend/plugins/base.py`.

### 1. Create your plugin file
Create a new Python file in `backend/plugins/`, e.g., `my_plugin.py`.

### 2. Implement the base class
```python
from .base import MetaPilotPlugin
from typing import Any, Dict, Optional

class MyCustomPlugin(MetaPilotPlugin):
    @property
    def name(self) -> str:
        return "MyCustomTool"

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        # Your logic here
        return {"status": "success", "data": "Handled task!"}
```

## 🧠 Integration

Plugins are automatically discovered by the `PluginManager` on startup. The `Orchestrator` checks if any plugin name matches keywords in a subtask's description and routes the execution accordingly.

## 🔌 MCP (Model Context Protocol) Support

MetaPilot AI also supports MCP-compatible servers. You can define a plugin that acts as an adapter to an external MCP server.

## 🛠️ Best Practices
- **Sandboxing**: Ensure your plugin doesn't perform destructive operations on the host system.
- **Error Handling**: Always return a consistent JSON structure with a `status` field.
- **Context**: Use the `context` parameter to access results of previous subtasks in a complex plan.
