"""Azure Blob helpers for scout backend assets.

The scout app keeps large datasets and model files in Azure Blob Storage.
This module centralizes the environment variable contract and provides small
download helpers that can be reused by button-specific services.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


DEFAULT_CONTAINER_ENV = "AZURE_STORAGE_CONTAINER_NAME"
DEFAULT_CONNECTION_ENV = "AZURE_STORAGE_CONNECTION_STRING"

DEFAULT_SCOUT_BACKEND_DATASET_BLOB = "02_scout_app/scouter_backend_player_dataset_2025_2026.csv"
DEFAULT_SCOUT_ONNX_INPUT_DATASET_BLOB = (
    "03_scout_model_input/scouter_onnx_salary_model_input_2025_2026.csv"
)
DEFAULT_SALARY_MODEL_CONFIG_BLOB = "04_model/model_config.json"
DEFAULT_SALARY_ONNX_MODEL_BLOB = "04_model/salary_prediction_model.onnx"
DEFAULT_SALARY_SKLEARN_MODEL_BLOB = "04_model/salary_prediction_model.pkl"


class BlobConfigurationError(RuntimeError):
    """Raised when Azure Blob configuration is missing or invalid."""


class ScoutBlobLoader:
    """Read scout CSV/model assets from Azure Blob Storage.

    Required environment variables:
    - AZURE_STORAGE_CONNECTION_STRING
    - AZURE_STORAGE_CONTAINER_NAME

    Blob path variables are optional because the current production paths are
    provided as defaults.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        container_name: str | None = None,
        cache_dir: str | Path | None = None,
    ) -> None:
        self.connection_string = connection_string or os.getenv(DEFAULT_CONNECTION_ENV)
        self.container_name = container_name or os.getenv(DEFAULT_CONTAINER_ENV)
        self.cache_dir = Path(cache_dir or os.getenv("SCOUT_BLOB_CACHE_DIR") or tempfile.gettempdir())

        if not self.connection_string:
            raise BlobConfigurationError(f"{DEFAULT_CONNECTION_ENV} is required")
        if not self.container_name:
            raise BlobConfigurationError(f"{DEFAULT_CONTAINER_ENV} is required")

        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError as exc:
            raise BlobConfigurationError(
                "azure-storage-blob is required to load scout assets from Azure Blob Storage"
            ) from exc

        service = BlobServiceClient.from_connection_string(self.connection_string)
        self._container = service.get_container_client(self.container_name)

    def download_bytes(self, blob_name: str) -> bytes:
        """Download a blob into memory."""
        return self._container.download_blob(blob_name).readall()

    def download_text(self, blob_name: str, encoding: str = "utf-8-sig") -> str:
        """Download a text blob and decode it."""
        return self.download_bytes(blob_name).decode(encoding)

    def download_to_cache(self, blob_name: str, filename: str | None = None) -> Path:
        """Download a blob to a local cache file and return the path."""
        safe_name = filename or blob_name.replace("/", "__")
        output_path = self.cache_dir / safe_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(self.download_bytes(blob_name))
        return output_path


def scout_blob_paths() -> dict[str, str]:
    """Return the configured scout Blob paths with production defaults."""
    return {
        "backend_dataset": os.getenv(
            "SCOUT_BACKEND_DATASET_BLOB",
            DEFAULT_SCOUT_BACKEND_DATASET_BLOB,
        ),
        "onnx_input_dataset": os.getenv(
            "SCOUT_ONNX_INPUT_DATASET_BLOB",
            DEFAULT_SCOUT_ONNX_INPUT_DATASET_BLOB,
        ),
        "salary_model_config": os.getenv(
            "SALARY_MODEL_CONFIG_BLOB",
            DEFAULT_SALARY_MODEL_CONFIG_BLOB,
        ),
        "salary_onnx_model": os.getenv(
            "SALARY_ONNX_MODEL_BLOB",
            DEFAULT_SALARY_ONNX_MODEL_BLOB,
        ),
        "salary_sklearn_model": os.getenv(
            "SALARY_SKLEARN_MODEL_BLOB",
            DEFAULT_SALARY_SKLEARN_MODEL_BLOB,
        ),
    }
