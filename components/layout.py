from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.constants import STYLE_DIR


CSS_FILES = [
    STYLE_DIR / "tokens.css",
    STYLE_DIR / "base.css",
    STYLE_DIR / "components.css",
    STYLE_DIR / "pages" / "home.css",
    STYLE_DIR / "pages" / "coach_squad.css",
    STYLE_DIR / "pages" / "coach_vs_squad.css",
    STYLE_DIR / "pages" / "coach_dashboard.css",
    STYLE_DIR / "pages" / "scout_search.css",
    STYLE_DIR / "pages" / "scout_result.css",
    STYLE_DIR / "pages" / "scout_market_dashboard.css",
]


def load_css() -> None:
    """Load global CSS files in a stable order."""
    css_chunks: list[str] = []

    for path in CSS_FILES:
        css_path = Path(path)
        if css_path.exists():
            css_chunks.append(css_path.read_text(encoding="utf-8"))

    if css_chunks:
        css = "\n\n".join(css_chunks)
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def app_header() -> None:
    mode = st.session_state.get("user_mode")
    mode_label = {
        "coach": "감독용",
        "scout": "스카우터용",
    }.get(mode, "모드 선택 전")

    st.markdown(
        f"""
        <div class="top-nav">
          <div class="brand">
            <div class="logo">MF</div>
            <div>
              <strong>Money Football</strong>
              <small>AI Football Squad & Scout Lab</small>
            </div>
          </div>
          <div class="status-pill">{mode_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"<h1 class='page-title'>{title}</h1>", unsafe_allow_html=True)

    if subtitle:
        st.markdown(f"<p class='page-subtitle'>{subtitle}</p>", unsafe_allow_html=True)


def section_title(title: str, description: str | None = None) -> None:
    st.markdown(f"### {title}")

    if description:
        st.caption(description)


def go_home_button() -> None:
    from components.navigation import move_page

    if st.button("홈으로 돌아가기"):
        move_page("home")
        st.rerun()
