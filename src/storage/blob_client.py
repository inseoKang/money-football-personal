from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st
from azure.storage.blob import BlobServiceClient


@st.cache_resource
def get_blob_service_client() -> BlobServiceClient:
    connection_string = st.secrets["azure_blob"]["connection_string"]
    return BlobServiceClient.from_connection_string(connection_string)


def get_container_client():
    container_name = st.secrets["azure_blob"]["container_name"]
    blob_service_client = get_blob_service_client()
    return blob_service_client.get_container_client(container_name)


@st.cache_data(ttl=3600)
def read_csv_from_blob(blob_path: str) -> pd.DataFrame:
    container_client = get_container_client()
    blob_client = container_client.get_blob_client(blob_path)

    blob_data = blob_client.download_blob().readall()
    csv_text = blob_data.decode("utf-8-sig")

    return pd.read_csv(StringIO(csv_text))


@st.cache_data(ttl=3600)
def read_bytes_from_blob(blob_path: str) -> bytes:
    container_client = get_container_client()
    blob_client = container_client.get_blob_client(blob_path)

    return blob_client.download_blob().readall()