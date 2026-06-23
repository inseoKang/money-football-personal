import pandas as pd
import streamlit as st

from src.coach.formation_run import get_available_formations
from src.coach.player_data import load_manager_players
from src.coach.vs_payload import compare_squads


@st.cache_data(show_spinner=False)
def _load_players():
    return load_manager_players()


def _metric_delta(value):
    if value > 0:
        return f"+{value:.2f}"
    return f"{value:.2f}"


def _render_summary_cards(title, summary):
    st.markdown(f"#### {title}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Players", f"{summary['players']:,}")
    col2.metric("Avg age", f"{summary['avg_age']:.1f}")
    col3.metric("Avg overall", f"{summary['avg_overall']:.1f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Minutes", f"{summary['total_minutes']:,}")
    col5.metric("Goals", f"{summary['total_goals']:,}")
    col6.metric("Assists", f"{summary['total_assists']:,}")


def _render_team_score(title, metrics):
    st.markdown(f"#### {title}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Team", f"{metrics['team_score']:.1f}", metrics["grade"])
    col2.metric("Attack", f"{metrics['attack']:.1f}")
    col3.metric("Midfield", f"{metrics['midfield']:.1f}")
    col4.metric("Defense", f"{metrics['defense']:.1f}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("GK", f"{metrics['keeper']:.1f}")
    col6.metric("Fit", f"{metrics['position_fit']:.1f}")
    col7.metric("Balance", f"{metrics['balance']:.1f}")
    col8.metric("Synergy", f"{metrics['synergy']:.1f}")


def _lineup_table(result):
    rows = []
    for slot in result["slots"]:
        player = slot.get("player")
        rows.append(
            {
                "Slot": slot["slotId"],
                "Role": slot["role"],
                "Player": "-" if not player else player["name"],
                "Club": "-" if not player else player["club"],
                "Pos": "-" if not player else player["positionGroup"],
                "Fit": round(float(slot.get("roleFitScore", 0)), 1),
            }
        )
    return pd.DataFrame(rows)


def _render_delta_table(comparison):
    metric_delta = comparison["delta"]["metrics"]
    rows = [
        {"Metric": "Team score", "Left - Right": _metric_delta(metric_delta["team_score"])},
        {"Metric": "Attack", "Left - Right": _metric_delta(metric_delta["attack"])},
        {"Metric": "Midfield", "Left - Right": _metric_delta(metric_delta["midfield"])},
        {"Metric": "Defense", "Left - Right": _metric_delta(metric_delta["defense"])},
        {"Metric": "Goalkeeper", "Left - Right": _metric_delta(metric_delta["keeper"])},
        {"Metric": "Position fit", "Left - Right": _metric_delta(metric_delta["position_fit"])},
        {"Metric": "Balance", "Left - Right": _metric_delta(metric_delta["balance"])},
        {"Metric": "Synergy", "Left - Right": _metric_delta(metric_delta["synergy"])},
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render():
    st.title("VS Squad")
    st.caption("Compare two clubs with the same formation using FM-style squad scores.")

    players = _load_players()

    control1, control2, control3 = st.columns([1.2, 1.2, 1])
    leagues = ["All"] + sorted(players["league"].dropna().unique().tolist())
    league = control1.selectbox("League filter", leagues)

    league_players = players if league == "All" else players[players["league"].eq(league)]
    clubs = sorted(league_players["club"].dropna().unique().tolist())

    if len(clubs) < 2:
        st.warning("At least two clubs are needed for VS comparison.")
        return

    left_club = control2.selectbox("Left club", clubs, index=0)
    default_right = 1 if len(clubs) > 1 else 0
    right_club = control3.selectbox("Right club", clubs, index=default_right)

    formation = st.selectbox("Formation", get_available_formations(), index=0)

    if left_club == right_club:
        st.info("Choose two different clubs to compare.")
        return

    left_players = league_players[league_players["club"].eq(left_club)].copy()
    right_players = league_players[league_players["club"].eq(right_club)].copy()

    comparison = compare_squads(left_players, right_players, formation)
    winner = comparison["winner"]

    if winner == "left":
        st.success(f"{left_club} has the stronger recommended lineup by team score.")
    elif winner == "right":
        st.success(f"{right_club} has the stronger recommended lineup by team score.")
    else:
        st.info("The recommended lineups are almost even by team score.")

    left_col, right_col = st.columns(2, gap="large")
    with left_col:
        _render_summary_cards(left_club, comparison["left"]["summary"])
        _render_team_score("Recommended lineup score", comparison["left"]["lineup"]["metrics"])
    with right_col:
        _render_summary_cards(right_club, comparison["right"]["summary"])
        _render_team_score("Recommended lineup score", comparison["right"]["lineup"]["metrics"])

    st.markdown("### Difference")
    _render_delta_table(comparison)

    left_lineup_tab, right_lineup_tab, payload_tab = st.tabs([f"{left_club} lineup", f"{right_club} lineup", "Payload"])
    with left_lineup_tab:
        st.dataframe(_lineup_table(comparison["left"]["lineup"]), use_container_width=True, hide_index=True)
        st.info(comparison["left"]["lineup"]["aiComment"])
    with right_lineup_tab:
        st.dataframe(_lineup_table(comparison["right"]["lineup"]), use_container_width=True, hide_index=True)
        st.info(comparison["right"]["lineup"]["aiComment"])
    with payload_tab:
        st.json(
            {
                "formation": comparison["formation"],
                "leftClub": left_club,
                "rightClub": right_club,
                "winner": comparison["winner"],
                "delta": comparison["delta"],
            }
        )
