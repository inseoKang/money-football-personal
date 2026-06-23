from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
STYLE_FILE = BASE_DIR / "styles" / "app.css"


def load_css() -> None:
    if STYLE_FILE.exists():
        st.markdown(f"<style>{STYLE_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def app_header() -> None:
    st.markdown(
        """
        <div class="app-header">
          <div>
            <strong>Money Football</strong>
            <span>Coach AI</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, description: str | None = None) -> None:
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if description:
        st.caption(description)
