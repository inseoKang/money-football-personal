"""앱 실행 환경과 개발자 기능 표시 여부를 관리합니다."""

from __future__ import annotations

import os


TRUE_VALUES = {"1", "true", "yes", "on"}


def is_development_mode() -> bool:
    """환경변수나 Streamlit 비밀 설정에서 개발 모드 여부를 확인합니다."""
    environment_value = os.getenv("APP_DEBUG", "").strip().lower()
    if environment_value in TRUE_VALUES:
        return True

    try:
        import streamlit as st

        secret_value = str(st.secrets.get("APP_DEBUG", "")).strip().lower()
        return secret_value in TRUE_VALUES
    except Exception:
        return False
