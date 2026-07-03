"""
MetaPilot AI - Markdown Exporter

Exports data to Markdown format.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

from .export_manager import Exporter, ExportConfig, ExportResult, ExportFormat

logger = logging.getLogger(__name__)


class MarkdownExporter(Exporter):
    """
    Exports data to Markdown format.
    
    Supports various data structures and converts them to Markdown.
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Initialize the Markdown exporter.
        
        Args:
            config: Export configuration
        """
        super().__init__(config)
    
    async def export(self, data: Any, output_path: Optional[str] = None) -> ExportResult:
        """
        Export data to a Markdown file.
        
        Args:
            data: Data to export
            output_path: Optional output file path
        
        Returns:
            ExportResult
        """
        import time
        start_time = time.time()
        
        try:
            # Convert data to Markdown
            markdown_content = await self.export_to_string(data)
            
            # Determine output path
            if output_path is None:
                output_dir = self._ensure_output_dir()
                filename = self._generate_filename("md")
                output_path = str(output_dir / filename)
            
            # Write to file
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding=self.config.encoding) as f:
                f.write(markdown_content)
            
            # Get file size
            file_size = Path(output_path).stat().st_size
            
            return ExportResult(
                success=True,
                file_path=output_path,
                content=markdown_content,
                format=ExportFormat.MARKDOWN,
                size=file_size,
                export_time=time.time() - start_time,
                metadata={
                    "type": "markdown",
                    "encoding": self.config.encoding
                }
            )
            
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {e}")
            return ExportResult(
                success=False,
                error=str(e),
                export_time=time.time() - start_time
            )
    
    async def export_to_string(self, data: Any) -> str:
        """
        Convert data to Markdown string.
        
        Args:
            data: Data to convert
        
        Returns:
            Markdown content
        """
        # Handle different data types
        if isinstance(data, str):
            return self._format_text(data)
        elif isinstance(data, dict):
            return self._format_dict(data)
        elif isinstance(data, list):
            return self._format_list(data)
        else:
            return self._format_primitive(data)
    
    def _format_text(self, text: str) -> str:
        """Format plain text as Markdown."""
        return text
    
    def _format_dict(self, data: Dict[str, Any], level: int = 0) -> str:
        """Format dictionary as Markdown."""
        lines = []
        
        for key, value in data.items():
            # Format key
            if level == 0:
                header_level = min(level + 2, 6)
                lines.append(f"{'#' * header_level} {key}")
            else:
                lines.append(f"\n**{key}**")
            
            # Format value
            if isinstance(value, dict):
                lines.append(self._format_dict(value, level + 1))
            elif isinstance(value, list):
                lines.append(self._format_list(value, level + 1))
            else:
                lines.append(f"{self._format_primitive(value)}")
        
        return "\n".join(lines)
    
    def _format_list(self, data: List[Any], level: int = 0) -> str:
        """Format list as Markdown."""
        if not data:
            return "- (empty)"
        
        lines = []
        
        for i, item in enumerate(data):
            if isinstance(item, dict):
                # For dicts in lists, format as sub-section
                header = f"#### Item {i+1}"
                lines.append(header)
                lines.append(self._format_dict(item, level + 1))
            elif isinstance(item, list):
                lines.append(self._format_list(item, level + 1))
            else:
                # Check if item is a simple value or needs formatting
                if isinstance(item, str) and '\n' in item:
                    # Multi-line string, add as code block or indented
                    lines.append(f"\n{item}\n")
                else:
                    lines.append(f"- {self._format_primitive(item)}")
        
        return "\n".join(lines)
    
    def _format_primitive(self, value: Any) -> str:
        """Format primitive values."""
        if value is None:
            return "_null_"
        elif isinstance(value, bool):
            return "✓" if value else "✗"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape special Markdown characters
            return value.replace('\\', '\\\\').replace('*', '\\*').replace('_', '\\_')
        elif isinstance(value, datetime):
            return value.isoformat()
        else:
            return str(value)
    
    def _format_table(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a Markdown table."""
        if not data:
            return ""
        
        # Get all keys
        keys = set()
        for row in data:
            keys.update(row.keys())
        
        sorted_keys = sorted(keys)
        
        # Create header
        header = "| " + " | ".join(sorted_keys) + " |"
        separator = "| " + " | ".join("-" * len(k) for k in sorted_keys) + " |"
        
        lines = [header, separator]
        
        # Add rows
        for row in data:
            cells = []
            for key in sorted_keys:
                value = row.get(key, "")
                if value is None:
                    value = ""
                elif isinstance(value, (dict, list)):
                    value = json.dumps(value)
                cells.append(str(value))
            lines.append("| " + " | ".join(cells) + " |")
        
        return "\n".join(lines)
    
    def _format_code(self, code: str, language: str = "") -> str:
        """Format code as Markdown code block."""
        if language:
            return f"```{language}\n{code}\n```"
        return f"```\n{code}\n```"
    
    def _format_quote(self, text: str, author: Optional[str] = None) -> str:
        """Format text as a quote."""
        if author:
            return f"> {text}\n> — {author}"
        return f"> {text}"


# Register with export manager
def register_markdown_exporter(export_manager: ExportManager, config: Optional[ExportConfig] = None) -> None:
    """Register the Markdown exporter with an export manager."""
    exporter = MarkdownExporter(config)
    export_manager.register_exporter(ExportFormat.MARKDOWN, exporter)
