"""Azure Blob Storage helpers for deployment smoke tests."""

from __future__ import annotations

from io import BytesIO

from services.azure_config import get_secret


CONNECTION_STRING_ENV = "AZURE_STORAGE_CONNECTION_STRING"
CONTAINER_ENV = "AZURE_STORAGE_CONTAINER"
CONTAINER_NAME_ENV = "AZURE_STORAGE_CONTAINER_NAME"
DEFAULT_CONTAINER = "money-football-data"


def _cache_data(func):
    try:
        import streamlit as st

        return st.cache_data(show_spinner=False)(func)
    except Exception:
        return func


def _container_name() -> str:
    return (
        get_secret(CONTAINER_ENV)
        or get_secret(CONTAINER_NAME_ENV)
        or DEFAULT_CONTAINER
    )


def get_blob_service_client():
    """Create an Azure BlobServiceClient from the configured connection string."""
    connection_string = get_secret(CONNECTION_STRING_ENV)
    if not connection_string:
        raise RuntimeError(f"{CONNECTION_STRING_ENV} is required")

    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:
        raise RuntimeError("azure-storage-blob is not installed") from exc

    try:
        return BlobServiceClient.from_connection_string(connection_string)
    except Exception as exc:
        raise RuntimeError(f"Failed to create BlobServiceClient: {exc}") from exc


def load_binary_from_blob(blob_path: str) -> bytes:
    """Load binary content from Azure Blob Storage."""
    if not blob_path:
        raise RuntimeError("blob_path is required")
    try:
        client = get_blob_service_client()
        blob_client = client.get_container_client(_container_name()).get_blob_client(blob_path)
        return blob_client.download_blob().readall()
    except Exception as exc:
        raise RuntimeError(f"Failed to read blob '{blob_path}': {exc}") from exc


@_cache_data
def load_csv_from_blob(blob_path: str) -> pd.DataFrame:
    """Load a UTF-8 CSV blob into a pandas DataFrame."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is not installed") from exc

    try:
        payload = load_binary_from_blob(blob_path)
        return pd.read_csv(BytesIO(payload), encoding="utf-8-sig")
    except Exception as exc:
        raise RuntimeError(f"Failed to load CSV blob '{blob_path}': {exc}") from exc
