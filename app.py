import streamlit as st

from components.layout import load_css, app_header
from components.navigation import infer_mode_from_page, render_sidebar_navigation

from views import home
from views.coach import squad as coach_squad
from views.coach import vs_squad as coach_vs_squad
from views.coach import dashboard as coach_dashboard
from views.scouter import search as scout_search
from views.scouter import result as scout_result
from views.scouter import market_dashboard as scout_market_dashboard


st.set_page_config(
    page_title="Money Football",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


PAGES = {
    "home": home.render,
    "coach_squad": coach_squad.render,
    "coach_vs_squad": coach_vs_squad.render,
    "coach_dashboard": coach_dashboard.render,
    "scout_search": scout_search.render,
    "scout_result": scout_result.render,
    "scout_market_dashboard": scout_market_dashboard.render,
}


def _first_query_value(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def main() -> None:
    load_css()

    st.session_state.setdefault("user_mode", None)
    st.session_state.setdefault("current_page", "home")

    page_from_query = _first_query_value(st.query_params.get("page"))

    if page_from_query in PAGES:
        st.session_state.current_page = page_from_query
        st.session_state.user_mode = infer_mode_from_page(page_from_query)

    page_key = st.session_state.get("current_page", "home")

    if page_key not in PAGES:
        page_key = "home"
        st.session_state.current_page = "home"
        st.session_state.user_mode = None

    app_header()

    if page_key != "home":
        render_sidebar_navigation()

    render_page = PAGES.get(page_key, home.render)
    render_page()


if __name__ == "__main__":
    main()