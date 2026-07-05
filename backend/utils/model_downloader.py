"""
Model Downloader for MetaPilot AI
"""

import logging
import os
from pathlib import Path
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

class ModelDownloader:
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    async def download_gguf(self, repo_id: str, filename: str) -> str:
        """
        Download a GGUF model from Hugging Face.
        """
        logger.info(f"Downloading {filename} from {repo_id}...")
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=self.models_dir,
            local_dir_use_symlinks=False
        )
        logger.info(f"Downloaded to {path}")
        return path

model_downloader = ModelDownloader()
