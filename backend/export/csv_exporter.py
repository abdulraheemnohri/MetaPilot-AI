"""
MetaPilot AI - CSV Exporter
"""

import logging
import csv
import io
from typing import Any, Dict, List, Optional
from .export_manager import Exporter, ExportConfig, ExportResult, ExportFormat

logger = logging.getLogger(__name__)

class CSVExporter(Exporter):
    def __init__(self, config: Optional[ExportConfig] = None):
        super().__init__(config)

    async def export_to_string(self, data: Any) -> str:
        if not isinstance(data, list):
            # If not a list, wrap it
            data = [data] if not isinstance(data, dict) else [data]

        if not data: return ""

        output = io.StringIO()
        # Flatten dicts if necessary
        keys = set()
        for item in data:
            if isinstance(item, dict): keys.update(item.keys())

        sorted_keys = sorted(list(keys)) if keys else ["value"]
        writer = csv.DictWriter(output, fieldnames=sorted_keys)
        writer.writeheader()

        for item in data:
            if isinstance(item, dict):
                writer.writerow({k: item.get(k, "") for k in sorted_keys})
            else:
                writer.writerow({sorted_keys[0]: str(item)})

        return output.getvalue()

    async def export(self, data: Any, output_path: Optional[str] = None) -> ExportResult:
        import time
        from pathlib import Path
        start_time = time.time()
        try:
            content = await self.export_to_string(data)
            if output_path is None:
                output_dir = self._ensure_output_dir()
                filename = self._generate_filename("csv")
                output_path = str(output_dir / filename)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return ExportResult(True, file_path=output_path, content=content, format=ExportFormat.CSV, size=len(content), export_time=time.time()-start_time)
        except Exception as e:
            return ExportResult(False, error=str(e), export_time=time.time()-start_time)

def register_csv_exporter(export_manager: Any, config: Optional[ExportConfig] = None) -> None:
    export_manager.register_exporter(ExportFormat.CSV, CSVExporter(config))
