from __future__ import annotations

import html

import streamlit as st

from components.cards import stat_card_html
from components.layout import page_title
from src.coach.dashboard import build_dashboard_payload
from src.coach.player_data import load_manager_players


def _rank_row(rank: int, row: dict) -> str:
    name = html.escape(str(row.get("player", "-")))
    club = html.escape(str(row.get("club", "-")))
    league = html.escape(str(row.get("league", "-")))
    position = html.escape(str(row.get("position", "-")))
    value = html.escape(str(row.get("value", "-")))

    return f"""
    <div class="market-list-card">
      <div class="market-list-main">
        <div class="market-list-title">{rank}. {name}</div>
        <div class="market-list-meta">{club} · {league} · {position}</div>
      </div>
      <div class="market-list-value">{value}</div>
    </div>
    """


def _summary_list_html(rows: list[dict], title_key: str) -> str:
    result = ""

    for row in rows:
        title = html.escape(str(row.get(title_key, "-")))
        league = html.escape(str(row.get("league", "")))
        players = html.escape(str(row.get("players", 0)))
        avg_overall = html.escape(str(row.get("avgOverall", 0)))
        goals = html.escape(str(row.get("goals", 0)))
        assists = html.escape(str(row.get("assists", 0)))
        sub = f"{league} · " if league and title_key == "club" else ""

        result += f"""
        <div class="market-list-card">
          <div class="market-list-main">
            <div class="market-list-title">{title}</div>
            <div class="market-list-meta">{sub}{players}명 · 득점 {goals} · 도움 {assists}</div>
          </div>
          <div class="market-list-value">{avg_overall}</div>
        </div>
        """

    return result


def render() -> None:
    st.markdown('<span class="scout-market-page-marker" aria-hidden="true"></span>', unsafe_allow_html=True)
    st.session_state.current_page = "scout_market_dashboard"
    st.session_state.user_mode = "scout"

    players = load_manager_players()

    if players.empty:
        st.error("선수 데이터가 비어 있습니다. data/manager_players.csv를 확인해 주세요.")
        return

    payload = build_dashboard_payload(players)
    summary = payload["summary"]

    page_title(
        "전체 선수 시장 대시보드",
        "리그/클럽별 선수단 분포와 주요 선수 랭킹을 스카우터 관점에서 확인합니다.",
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card_html("전체 선수", summary["players"], "분석 대상 선수 수"), unsafe_allow_html=True)
    c2.markdown(stat_card_html("리그", summary["leagues"], "소속 리그 수"), unsafe_allow_html=True)
    c3.markdown(stat_card_html("클럽", summary["clubs"], "소속 클럽 수"), unsafe_allow_html=True)
    c4.markdown(stat_card_html("평균 종합", summary["avgOverall"], "overall_score 평균"), unsafe_allow_html=True)

    st.divider()

    st.markdown("### TOP 선수 랭킹")
    tabs = st.tabs(["종합", "공격", "수비", "골키퍼", "득점", "도움"])
    top_map = [
        ("overall", tabs[0]),
        ("attack", tabs[1]),
        ("defense", tabs[2]),
        ("keeper", tabs[3]),
        ("goals", tabs[4]),
        ("assists", tabs[5]),
    ]

    for key, tab in top_map:
        with tab:
            rows = payload["topPlayers"].get(key, [])
            if not rows:
                st.info("표시할 선수가 없습니다.")
                continue
            cols = st.columns(2)
            for idx, row in enumerate(rows, start=1):
                with cols[(idx - 1) % 2]:
                    st.markdown(_rank_row(idx, row), unsafe_allow_html=True)

    st.divider()

    league_col, club_col = st.columns(2, gap="large")

    with league_col:
        st.markdown("### 리그별 요약")
        st.markdown(_summary_list_html(payload["leagueSummary"], "league"), unsafe_allow_html=True)

    with club_col:
        st.markdown("### 클럽별 요약 TOP 12")
        st.markdown(_summary_list_html(payload["clubSummary"], "club"), unsafe_allow_html=True)
