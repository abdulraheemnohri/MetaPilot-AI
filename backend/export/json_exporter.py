"""
MetaPilot AI - JSON Exporter

Exports data to JSON format.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

from .export_manager import Exporter, ExportConfig, ExportResult, ExportFormat

logger = logging.getLogger(__name__)


class JSONExporter(Exporter):
    """
    Exports data to JSON format.
    
    Supports pretty printing and custom serialization.
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Initialize the JSON exporter.
        
        Args:
            config: Export configuration
        """
        super().__init__(config)
    
    async def export(self, data: Any, output_path: Optional[str] = None) -> ExportResult:
        """
        Export data to a JSON file.
        
        Args:
            data: Data to export
            output_path: Optional output file path
        
        Returns:
            ExportResult
        """
        import time
        start_time = time.time()
        
        try:
            # Convert data to JSON string
            json_content = await self.export_to_string(data)
            
            # Determine output path
            if output_path is None:
                output_dir = self._ensure_output_dir()
                filename = self._generate_filename("json")
                output_path = str(output_dir / filename)
            
            # Write to file
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding=self.config.encoding) as f:
                f.write(json_content)
            
            # Get file size
            file_size = Path(output_path).stat().st_size
            
            return ExportResult(
                success=True,
                file_path=output_path,
                content=json_content,
                format=ExportFormat.JSON,
                size=file_size,
                export_time=time.time() - start_time,
                metadata={
                    "type": "json",
                    "encoding": self.config.encoding,
                    "pretty_print": self.config.pretty_print
                }
            )
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return ExportResult(
                success=False,
                error=str(e),
                export_time=time.time() - start_time
            )
    
    async def export_to_string(self, data: Any) -> str:
        """
        Convert data to JSON string.
        
        Args:
            data: Data to convert
        
        Returns:
            JSON content
        """
        # Create a copy of the data to avoid modifying the original
        export_data = self._prepare_data(data)
        
        # Serialize to JSON
        indent = 2 if self.config.pretty_print else None
        ensure_ascii = False
        
        return json.dumps(export_data, indent=indent, ensure_ascii=ensure_ascii, default=self._serialize_default)
    
    def _prepare_data(self, data: Any) -> Any:
        """
        Prepare data for JSON serialization.
        
        Converts non-serializable types to serializable ones.
        """
        if isinstance(data, dict):
            return {k: self._prepare_data(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._prepare_data(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, bytes):
            return data.decode('utf-8', errors='replace')
        elif isinstance(data, set):
            return list(data)
        elif hasattr(data, '__dict__'):
            # Convert objects to dicts
            return {k: self._prepare_data(v) for k, v in vars(data).items()}
        elif isinstance(data, (int, float, str, bool, type(None))):
            return data
        else:
            # Try to convert to string
            return str(data)
    
    def _serialize_default(self, obj: Any) -> Any:
        """
        Default serialization for non-serializable objects.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        elif hasattr(obj, '__dict__'):
            return vars(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        else:
            return str(obj)


# Register with export manager
def register_json_exporter(export_manager: Any, config: Optional[ExportConfig] = None) -> None:
    """Register the JSON exporter with an export manager."""
    exporter = JSONExporter(config)
    export_manager.register_exporter(ExportFormat.JSON, exporter)
