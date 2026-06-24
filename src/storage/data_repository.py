from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.storage.blob_client import read_csv_from_blob


def is_blob_enabled() -> bool:
    try:
        azure_blob = st.secrets.get("azure_blob")
        if not azure_blob:
            return False

        return bool(
            azure_blob.get("connection_string")
            and azure_blob.get("container_name")
        )
    except Exception:
        return False


@st.cache_data(ttl=3600)
def read_csv(blob_path: str, local_path: str | Path) -> pd.DataFrame:
    """
    Blob Storage 연결 전/후를 모두 지원하는 CSV 로더입니다.

    - Blob 설정이 있으면 Azure Blob Storage에서 읽음
    - Blob 설정이 없으면 로컬 CSV에서 읽음
    """

    if is_blob_enabled():
        return read_csv_from_blob(blob_path)

    return pd.read_csv(local_path)