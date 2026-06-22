from __future__ import annotations

import streamlit as st


COACH_PAGES = {
    "내 스쿼드": "coach_squad",
    "VS 스쿼드": "coach_vs_squad",
    "선수 대시보드": "coach_dashboard",
}

SCOUT_PAGES = {
    "스카우팅 검색": "scout_search",
    "스카우팅 결과": "scout_result",
}

COACH_PAGE_KEYS = set(COACH_PAGES.values())
SCOUT_PAGE_KEYS = set(SCOUT_PAGES.values())


def infer_mode_from_page(page_key: str | None) -> str | None:
    if page_key in COACH_PAGE_KEYS:
        return "coach"
    if page_key in SCOUT_PAGE_KEYS:
        return "scout"
    return None


def _clear_query_and_set_page(page_key: str) -> None:
    st.query_params.clear()

    if page_key != "home":
        st.query_params["page"] = page_key


def move_page(page_key: str) -> None:
    st.session_state.current_page = page_key
    st.session_state.user_mode = infer_mode_from_page(page_key)
    _clear_query_and_set_page(page_key)


def set_mode(mode: str) -> None:
    if mode == "coach":
        move_page("coach_squad")
    elif mode == "scout":
        move_page("scout_search")
    else:
        move_page("home")


def render_sidebar_navigation() -> None:
    mode = st.session_state.get("user_mode")

    with st.sidebar:
        st.markdown("## Money Football")

        if st.button("🏠 메인", use_container_width=True):
            move_page("home")
            st.rerun()

        st.divider()

        if mode == "coach":
            st.markdown("### 감독용 메뉴")
            pages = COACH_PAGES
        elif mode == "scout":
            st.markdown("### 스카우터용 메뉴")
            pages = SCOUT_PAGES
        else:
            pages = {}

        for label, page_key in pages.items():
            is_active = st.session_state.current_page == page_key
            button_label = f"✅ {label}" if is_active else label

            if st.button(button_label, use_container_width=True):
                move_page(page_key)
                st.rerun()

        st.divider()

        if st.button("🔄 모드 다시 선택", use_container_width=True):
            move_page("home")
            st.rerun()