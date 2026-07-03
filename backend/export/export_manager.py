"""
MetaPilot AI - Export Manager

Manages export of results and data to various formats.
"""

import logging
import os
import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    TEXT = "text"
    CSV = "csv"
    PDF = "pdf"
    DOCX = "docx"


@dataclass
class ExportConfig:
    """Configuration for export operations."""
    format: ExportFormat = ExportFormat.MARKDOWN
    output_dir: str = "exports"
    filename_prefix: str = "export"
    include_metadata: bool = True
    include_timestamp: bool = True
    pretty_print: bool = True
    encoding: str = "utf-8"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format.value,
            "output_dir": self.output_dir,
            "filename_prefix": self.filename_prefix,
            "include_metadata": self.include_metadata,
            "include_timestamp": self.include_timestamp,
            "pretty_print": self.pretty_print,
            "encoding": self.encoding
        }


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    file_path: Optional[str] = None
    content: Optional[str] = None
    format: Optional[ExportFormat] = None
    size: int = 0
    export_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "file_path": self.file_path,
            "format": self.format.value if self.format else None,
            "size": self.size,
            "export_time": self.export_time,
            "error": self.error,
            "metadata": self.metadata
        }


class Exporter:
    """Base class for exporters."""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Initialize the exporter.
        
        Args:
            config: Export configuration
        """
        self.config = config or ExportConfig()
    
    async def export(self, data: Any, output_path: Optional[str] = None) -> ExportResult:
        """
        Export data to a file.
        
        Args:
            data: Data to export
            output_path: Optional output file path
        
        Returns:
            ExportResult
        """
        raise NotImplementedError("Subclasses must implement export()")
    
    async def export_to_string(self, data: Any) -> str:
        """
        Export data to a string.
        
        Args:
            data: Data to export
        
        Returns:
            Exported content as string
        """
        raise NotImplementedError("Subclasses must implement export_to_string()")
    
    def _generate_filename(self, extension: str, prefix: Optional[str] = None) -> str:
        """Generate a filename for export."""
        prefix = prefix or self.config.filename_prefix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if self.config.include_timestamp else ""
        
        if timestamp:
            return f"{prefix}_{timestamp}.{extension}"
        return f"{prefix}.{extension}"
    
    def _ensure_output_dir(self, output_dir: Optional[str] = None) -> Path:
        """Ensure output directory exists."""
        dir_path = Path(output_dir or self.config.output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path


class ExportManager:
    """
    Main export manager class.
    
    Manages multiple exporters and provides a unified interface.
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Initialize the export manager.
        
        Args:
            config: Default export configuration
        """
        self.config = config or ExportConfig()
        self._exporters: Dict[ExportFormat, Exporter] = {}
        self._lock = asyncio.Lock()
    
    def register_exporter(self, format: ExportFormat, exporter: Exporter) -> None:
        """
        Register an exporter for a specific format.
        
        Args:
            format: Export format
            exporter: Exporter instance
        """
        self._exporters[format] = exporter
        logger.info(f"Registered exporter for format: {format.value}")
    
    def get_exporter(self, format: ExportFormat) -> Optional[Exporter]:
        """Get an exporter by format."""
        return self._exporters.get(format)
    
    async def export(self, 
                    data: Any,
                    format: ExportFormat = ExportFormat.MARKDOWN,
                    output_path: Optional[str] = None,
                    config: Optional[ExportConfig] = None) -> ExportResult:
        """
        Export data to a file.
        
        Args:
            data: Data to export
            format: Export format
            output_path: Optional output file path
            config: Optional export configuration
        
        Returns:
            ExportResult
        """
        import time
        start_time = time.time()
        
        try:
            # Use provided config or default
            export_config = config or self.config
            
            # Get exporter
            exporter = self.get_exporter(format)
            if not exporter:
                return ExportResult(
                    success=False,
                    error=f"No exporter registered for format: {format.value}"
                )
            
            # Generate output path if not provided
            if output_path is None:
                output_dir = export_config.output_dir
                extension = format.value
                filename = exporter._generate_filename(extension)
                output_path = str(Path(output_dir) / filename)
            
            # Export
            result = await exporter.export(data, output_path)
            
            # Update with timing
            result.export_time = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return ExportResult(
                success=False,
                error=str(e),
                export_time=time.time() - start_time
            )
    
    async def export_to_string(self, 
                              data: Any,
                              format: ExportFormat = ExportFormat.MARKDOWN,
                              config: Optional[ExportConfig] = None) -> str:
        """
        Export data to a string.
        
        Args:
            data: Data to export
            format: Export format
            config: Optional export configuration
        
        Returns:
            Exported content as string
        """
        # Get exporter
        exporter = self.get_exporter(format)
        if not exporter:
            raise ValueError(f"No exporter registered for format: {format.value}")
        
        return await exporter.export_to_string(data)
    
    async def export_batch(self, 
                          data_list: List[Any],
                          format: ExportFormat = ExportFormat.MARKDOWN,
                          output_dir: Optional[str] = None,
                          filename_prefix: Optional[str] = None) -> List[ExportResult]:
        """
        Export multiple data items to files.
        
        Args:
            data_list: List of data items to export
            format: Export format
            output_dir: Optional output directory
            filename_prefix: Optional filename prefix
        
        Returns:
            List of ExportResult objects
        """
        results = []
        
        for i, data in enumerate(data_list):
            # Generate unique filename for each item
            prefix = filename_prefix or f"{self.config.filename_prefix}_{i+1}"
            config = ExportConfig(
                format=format,
                output_dir=output_dir or self.config.output_dir,
                filename_prefix=prefix,
                include_timestamp=self.config.include_timestamp
            )
            
            result = await self.export(data, format, config=config)
            results.append(result)
        
        return results
    
    def list_formats(self) -> List[ExportFormat]:
        """List all supported export formats."""
        return list(self._exporters.keys())
    
    def has_format(self, format: ExportFormat) -> bool:
        """Check if a format is supported."""
        return format in self._exporters


# Global export manager instance
export_manager = None


def get_export_manager(config: Optional[ExportConfig] = None) -> ExportManager:
    """Get or create the global export manager."""
    global export_manager
    if export_manager is None:
        export_manager = ExportManager(config)
    return export_manager
