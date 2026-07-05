"""
Export Module for MetaPilot AI
"""

from .export_manager import (
    ExportManager,
    ExportFormat,
    ExportConfig,
    ExportResult,
    get_export_manager
)
from .markdown_exporter import register_markdown_exporter
from .html_exporter import register_html_exporter
from .json_exporter import register_json_exporter
from .csv_exporter import register_csv_exporter

# Initialize and register default exporters
def init_export_system():
    manager = get_export_manager()
    register_markdown_exporter(manager)
    register_html_exporter(manager)
    register_json_exporter(manager)
    register_csv_exporter(manager)
    return manager

export_manager = init_export_system()

__all__ = [
    "ExportManager",
    "ExportFormat",
    "ExportConfig",
    "ExportResult",
    "export_manager",
    "get_export_manager"
]
