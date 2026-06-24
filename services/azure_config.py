"""Configuration helpers for Azure Web App and local Streamlit runs."""

from __future__ import annotations

import os
from typing import Any


def get_secret(key: str, default: Any = None) -> Any:
    """Read a config value from env first, then Streamlit secrets.

    Azure Web App should use Application Settings. Local Streamlit runs can use
    .streamlit/secrets.toml, but this function also works outside Streamlit.
    """
    value = os.getenv(key)
    if value not in {None, ""}:
        return value

    try:
        import streamlit as st

        return st.secrets.get(key, default)
    except Exception:
        return default


def has_secret(key: str) -> bool:
    """Return True when a secret/config value is available without exposing it."""
    value = get_secret(key)
    return value not in {None, ""}
