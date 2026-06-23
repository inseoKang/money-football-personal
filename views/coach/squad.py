import pandas as pd
import streamlit as st

from src.coach.formation_run import get_available_formations, get_formation_slots
from src.coach.lineup_payload import recommend_lineup_payload
from src.coach.player_data import load_manager_players


POSITION_LABELS = {
    "GK": "GK",
    "DF": "DF",
    "MF": "MF",
    "FW": "FW",
}

DISPLAY_COLUMNS = [
    "salary_id",
    "player",
    "club",
    "league",
    "position_group",
    "age",
    "matches",
    "minutes",
    "goals",
    "assists",
    "overall_score",
    "attack_score",
    "defense_score",
    "keeper_score",
]

COLUMN_LABELS = {
    "salary_id": "ID",
    "player": "Player",
    "club": "Club",
    "league": "League",
    "position_group": "Pos",
    "age": "Age",
    "matches": "Matches",
    "minutes": "Minutes",
    "goals": "Goals",
    "assists": "Assists",
    "overall_score": "Overall",
    "attack_score": "Attack",
    "defense_score": "Defense",
    "keeper_score": "GK",
}


@st.cache_data(show_spinner=False)
def _load_players():
    return load_manager_players()


def _filter_players(players, league, club, position, keyword):
    filtered = players.copy()

    if league != "All":
        filtered = filtered[filtered["league"].eq(league)]

    if club != "All":
        filtered = filtered[filtered["club"].eq(club)]

    if position != "All":
        filtered = filtered[filtered["position_group"].eq(position)]

    if keyword:
        keyword_lower = keyword.strip().lower()
        filtered = filtered[
            filtered["player"].str.lower().str.contains(keyword_lower, na=False)
            | filtered["club"].str.lower().str.contains(keyword_lower, na=False)
        ]

    return filtered


def _format_position(value):
    return POSITION_LABELS.get(value, value)


def _score_bar(label, value):
    value = 0 if pd.isna(value) else float(value)
    st.progress(min(max(value / 100, 0), 1), text=f"{label} {value:.1f}")


def _render_summary(players):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Players", f"{len(players):,}")
    col2.metric("Avg age", f"{players['age'].mean():.1f}")
    col3.metric("Goals", f"{int(players['goals'].sum()):,}")
    col4.metric("Assists", f"{int(players['assists'].sum()):,}")


def _render_player_detail(player):
    st.subheader(player["player"])
    st.caption(
        f"{_format_position(player['position_group'])} / {player['club']} / "
        f"{player['league']} / Age {int(player['age'])} / {player['country']}"
    )

    score_col, stat_col = st.columns([1, 1])

    with score_col:
        st.markdown("#### FM-style scores")
        _score_bar("Overall", player["overall_score"])
        _score_bar("Attack", player["attack_score"])
        _score_bar("Defense", player["defense_score"])
        _score_bar("Goalkeeper", player["keeper_score"])
        _score_bar("Stamina", player["stamina_score"])
        _score_bar("Discipline", player["discipline_score"])

    with stat_col:
        st.markdown("#### Key records")
        c1, c2, c3 = st.columns(3)
        c1.metric("Matches", int(player["matches"]))
        c2.metric("Starts", int(player["starts"]))
        c3.metric("Minutes", f"{int(player['minutes']):,}")

        c4, c5, c6 = st.columns(3)
        c4.metric("Goals", int(player["goals"]))
        c5.metric("Assists", int(player["assists"]))
        c6.metric("SOT", int(player["shots_on_target"]))

        c7, c8, c9 = st.columns(3)
        c7.metric("Interceptions", int(player["interceptions"]))
        c8.metric("Tackles won", int(player["tackles_won"]))
        c9.metric("Clean sheets", int(player["clean_sheets"]))


def _render_metric_cards(metrics):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Team score", f"{metrics['team_score']:.1f}", metrics["grade"])
    col2.metric("Attack", f"{metrics['attack']:.1f}")
    col3.metric("Midfield", f"{metrics['midfield']:.1f}")
    col4.metric("Defense", f"{metrics['defense']:.1f}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Goalkeeper", f"{metrics['keeper']:.1f}")
    col6.metric("Position fit", f"{metrics['position_fit']:.1f}")
    col7.metric("Balance", f"{metrics['balance']:.1f}")
    col8.metric("Synergy", f"{metrics['synergy']:.1f}")


def _render_lineup_table(players, formation, lineup):
    slots = get_formation_slots(formation)
    rows = []

    for slot in slots:
        player_name = lineup.get(slot["slot_id"])
        player_info = None
        if player_name:
            matched = players[players["player"].eq(player_name)]
            if not matched.empty:
                player_info = matched.iloc[0]

        rows.append(
            {
                "Slot": slot["slot_id"],
                "Role": slot["role"],
                "Line": slot["line"],
                "Player": player_name or "-",
                "Club": "-" if player_info is None else player_info["club"],
                "Pos": "-" if player_info is None else player_info["position_group"],
                "Overall": "-" if player_info is None else round(float(player_info["overall_score"]), 1),
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_pitch_view(formation, lineup):
    slots = get_formation_slots(formation)
    lines = ["FW", "MF", "DF", "GK"]

    st.markdown("#### Formation board")
    for line in lines:
        line_slots = [slot for slot in slots if slot["line"] == line]
        if not line_slots:
            continue

        columns = st.columns(len(line_slots))
        for column, slot in zip(columns, line_slots):
            player_name = lineup.get(slot["slot_id"]) or "Empty"
            short_name = player_name if len(player_name) <= 22 else player_name[:19] + "..."
            column.markdown(
                f"""
                <div style="border:1px solid #d8e0ec;border-radius:8px;padding:10px;text-align:center;background:#ffffff;margin-bottom:8px;min-height:82px;">
                    <div style="font-size:12px;color:#64748b;">{slot['slot_id']} / {slot['role']}</div>
                    <div style="font-weight:700;margin-top:6px;">{short_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_lineup_evaluation(players):
    st.markdown("---")
    st.markdown("## Lineup evaluation")
    st.caption("Choose a formation and let Coach AI recommend a lineup from the currently filtered squad.")

    if len(players) < 11:
        st.info("At least 11 players are needed for lineup evaluation. Loosen the filters first.")
        return

    formation = st.selectbox("Formation", get_available_formations(), index=0)
    result = recommend_lineup_payload(players, formation)
    metrics = result["metrics"]
    lineup_by_id = result["lineup"]
    lineup_by_name = {
        slot["slotId"]: slot["player"]["name"] if slot.get("player") else None
        for slot in result["slots"]
    }

    _render_metric_cards(metrics)

    source_label = "Azure OpenAI" if result["commentSource"] == "azure_openai" else "Fallback rule"
    st.info(f"{result['aiComment']}\n\nSource: {source_label}")

    if result["commentSource"] == "fallback":
        with st.expander("Azure OpenAI fallback detail"):
            st.caption(result["commentError"])
            st.code(result["promptPreview"][:2000])

    board_tab, table_tab, payload_tab = st.tabs(["Board", "Table", "Payload"])
    with board_tab:
        _render_pitch_view(formation, lineup_by_name)
    with table_tab:
        _render_lineup_table(players, formation, lineup_by_name)
    with payload_tab:
        st.json({
            "formation": formation,
            "lineup": lineup_by_id,
            "metrics": metrics,
            "commentSource": result["commentSource"],
            "warnings": result["warnings"],
        })


def render():
    st.title("Coach Squad")
    st.caption("Browse 2025-2026 player data and FM-style scores for the coach page.")

    players = _load_players()

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1.1, 1.2, 1, 1.5])

    leagues = ["All"] + sorted(players["league"].dropna().unique().tolist())
    league = filter_col1.selectbox("League", leagues)

    club_source = players if league == "All" else players[players["league"].eq(league)]
    clubs = ["All"] + sorted(club_source["club"].dropna().unique().tolist())
    club = filter_col2.selectbox("Club", clubs)

    positions = ["All", "GK", "DF", "MF", "FW"]
    position = filter_col3.selectbox("Position", positions)

    keyword = filter_col4.text_input("Search", placeholder="Haaland, Real Madrid")

    filtered = _filter_players(players, league, club, position, keyword)

    if filtered.empty:
        st.warning("No players match the selected filters.")
        return

    _render_summary(filtered)

    sort_options = {
        "Overall high": "overall_score",
        "Attack high": "attack_score",
        "Defense high": "defense_score",
        "Minutes high": "minutes",
        "Goals high": "goals",
        "Assists high": "assists",
        "Age young": "age",
    }
    sort_label = st.selectbox("Sort", list(sort_options.keys()), index=0)
    sort_column = sort_options[sort_label]
    ascending = sort_label == "Age young"
    filtered = filtered.sort_values(sort_column, ascending=ascending)

    table = filtered[DISPLAY_COLUMNS].copy()
    table["position_group"] = table["position_group"].map(_format_position)
    table = table.rename(columns=COLUMN_LABELS)

    st.markdown("### Player list")
    st.dataframe(table, use_container_width=True, hide_index=True, height=430)

    st.markdown("### Player detail")
    player_options = filtered["player"].tolist()
    selected_player = st.selectbox("Select player", player_options)
    selected_row = filtered[filtered["player"].eq(selected_player)].iloc[0]
    _render_player_detail(selected_row)

    _render_lineup_evaluation(filtered)

