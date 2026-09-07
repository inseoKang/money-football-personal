from __future__ import annotations

import streamlit as st


COACH_PAGES = {
    "내 스쿼드": "coach_squad",
    "VS 스쿼드": "coach_vs_squad",
    "선수 대시보드": "coach_dashboard",
}

SCOUT_PAGES = {
    "스카우팅 검색": "scout_search",
    "전체 선수 시장 대시보드": "scout_market_dashboard",
}

COACH_PAGE_KEYS = set(COACH_PAGES.values())

# scout_result는 사이드바에는 보이지 않지만,
# 검색 조건 설정 후 결과 페이지로 이동할 수 있어야 하므로 모드 판별에는 포함합니다.
SCOUT_PAGE_KEYS = set(SCOUT_PAGES.values()) | {"scout_result"}


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

        if st.button("홈 화면으로 이동", width="stretch"):
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

            if st.button(
                label,
                key=f"sidebar_nav_{page_key}",
                type="primary" if is_active else "secondary",
                width="stretch",
            ):
                move_page(page_key)
                st.rerun()

        st.divider()