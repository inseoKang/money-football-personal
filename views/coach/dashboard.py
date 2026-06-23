import pandas as pd
import streamlit as st

from src.coach.dashboard import build_dashboard_payload
from src.coach.player_data import load_manager_players


@st.cache_data(show_spinner=False)
def _load_players():
    return load_manager_players()


def _records_to_df(records):
    return pd.DataFrame(records)


def _render_summary(summary):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Players", f"{summary['players']:,}")
    col2.metric("Leagues", f"{summary['leagues']:,}")
    col3.metric("Clubs", f"{summary['clubs']:,}")
    col4.metric("Avg overall", f"{summary['avgOverall']:.1f}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Avg age", f"{summary['avgAge']:.1f}")
    col6.metric("Avg minutes", f"{summary['avgMinutes']:.0f}")
    col7.metric("Goals", f"{summary['totalGoals']:,}")
    col8.metric("Assists", f"{summary['totalAssists']:,}")


def _render_position_charts(payload):
    position_df = _records_to_df(payload["positionDistribution"])
    score_df = _records_to_df(payload["positionScores"])

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("### Position distribution")
        st.bar_chart(position_df.set_index("position")["players"])

    with right:
        st.markdown("### Average FM-style scores by position")
        chart_df = score_df.set_index("position_group")[["overall", "attack", "defense", "stamina"]]
        st.bar_chart(chart_df)


def _render_league_and_club_tables(payload):
    league_df = _records_to_df(payload["leagueSummary"])
    club_df = _records_to_df(payload["clubSummary"])

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("### League summary")
        st.dataframe(league_df, use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Top clubs by average overall")
        st.dataframe(club_df, use_container_width=True, hide_index=True)


def _render_top_players(payload):
    st.markdown("### Top players")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Overall", "Attack", "Defense", "Goalkeeper", "Goals", "Assists"]
    )

    top_players = payload["topPlayers"]
    tabs = [
        (tab1, "overall"),
        (tab2, "attack"),
        (tab3, "defense"),
        (tab4, "keeper"),
        (tab5, "goals"),
        (tab6, "assists"),
    ]

    for tab, key in tabs:
        with tab:
            df = _records_to_df(top_players[key])
            if df.empty:
                st.info("No data available.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)


def render():
    st.title("Coach Dashboard")
    st.caption("A quick squad intelligence dashboard based on 2025-2026 player data.")

    players = _load_players()

    league_col, club_col = st.columns(2)
    leagues = ["All"] + sorted(players["league"].dropna().unique().tolist())
    league = league_col.selectbox("League", leagues)

    league_players = players if league == "All" else players[players["league"].eq(league)]
    clubs = ["All"] + sorted(league_players["club"].dropna().unique().tolist())
    club = club_col.selectbox("Club", clubs)

    filtered = league_players if club == "All" else league_players[league_players["club"].eq(club)]

    if filtered.empty:
        st.warning("No dashboard data for the selected filter.")
        return

    payload = build_dashboard_payload(filtered)

    _render_summary(payload["summary"])
    _render_position_charts(payload)
    _render_league_and_club_tables(payload)
    _render_top_players(payload)

    with st.expander("Dashboard payload"):
        st.json(payload)

