from __future__ import annotations

import html
from textwrap import dedent

import streamlit as st

from components.layout import page_title
from src.coach.dashboard import build_dashboard_payload
from src.coach.player_data import load_barcelona_players


METRIC_LABELS = {
    "overall": "종합",
    "attack": "공격",
    "defense": "수비",
    "keeper": "골키퍼",
    "goals": "득점",
    "assists": "도움",
}


def _kpi_card(label: str, value, caption: str = "", wide: bool = False) -> str:
    wide_class = " wide" if wide else ""

    return dedent(
        f"""
        <div class="dashboard-kpi-card{wide_class}">
          <div class="dashboard-kpi-label">{html.escape(str(label))}</div>
          <div class="dashboard-kpi-value">{html.escape(str(value))}</div>
          <div class="dashboard-kpi-caption">{html.escape(str(caption))}</div>
        </div>
        """
    ).strip()


def _summary_metrics_html(summary: dict) -> str:
    cards = [
        _kpi_card("바르셀로나 선수", summary["players"], "분석 대상 선수 수"),
        _kpi_card("평균 종합", summary["avgOverall"], "overall_score 평균"),
        _kpi_card("총 득점", summary["totalGoals"], "전체 득점 합계"),
        _kpi_card("총 도움", summary["totalAssists"], "전체 도움 합계"),
        _kpi_card("평균 나이", summary["avgAge"], "선수단 평균 연령"),
        _kpi_card("평균 출전시간", summary["avgMinutes"], "minutes 평균"),
        _kpi_card("소속 클럽", "FC Barcelona", "감독용 고정 팀", wide=True),
    ]

    return dedent(
        f"""
        <div class="dashboard-panel compact">
          <div class="dashboard-section-title">선수단 요약</div>
          <div class="top-summary-grid">
            {"".join(cards)}
          </div>
        </div>
        """
    ).strip()


def _position_distribution_html(rows: list[dict]) -> str:
    cards = ""

    for row in rows:
        position = html.escape(str(row.get("position", "-")))
        players = html.escape(str(row.get("players", 0)))

        cards += dedent(
            f"""
            <div class="position-card">
              <strong>{players}</strong>
              <span>{position}</span>
            </div>
            """
        ).strip()

    return dedent(
        f"""
        <div class="dashboard-panel compact">
          <div class="dashboard-section-title">포지션 구성</div>
          <div class="position-grid-2x2">
            {cards}
          </div>
        </div>
        """
    ).strip()


def _position_score_html(rows: list[dict]) -> str:
    html_rows = ""

    for row in rows:
        position = html.escape(str(row.get("position_group", "-")))
        players = html.escape(str(row.get("players", 0)))
        overall = html.escape(str(row.get("overall", 0)))

        chips = ""

        for key, label in [
            ("attack", "공격"),
            ("defense", "수비"),
            ("keeper", "키퍼"),
            ("stamina", "체력"),
            ("discipline", "규율"),
        ]:
            value = html.escape(str(row.get(key, 0)))
            chips += f"<div class='score-chip'>{label} {value}</div>"

        html_rows += dedent(
            f"""
            <div class="position-score-card">
              <div class="score-card-head">
                <div>
                  <div class="score-position">{position}</div>
                  <div class="score-overall">{overall}</div>
                </div>
                <div class="score-count">{players}명</div>
              </div>
              <div class="score-chip-row">{chips}</div>
            </div>
            """
        ).strip()

    return dedent(
        f"""
        <div class="position-score-grid">
          {html_rows}
        </div>
        """
    ).strip()


def _rank_row(rank: int, row: dict) -> str:
    name = html.escape(str(row.get("player", "-")))
    position = html.escape(str(row.get("position", "-")))
    value = html.escape(str(row.get("value", "-")))
    overall = html.escape(str(row.get("overall", "-")))

    return dedent(
        f"""
        <div class="mini-rank-card">
          <div>
            <div class="mini-rank-name">{rank}. {name}</div>
            <div class="mini-rank-meta">{position} · 종합 {overall}</div>
          </div>
          <div class="mini-rank-value">{value}</div>
        </div>
        """
    ).strip()


def _first_query_value(value, default: str = "") -> str:
    if isinstance(value, list):
        return str(value[0]) if value else default

    if value is None:
        return default

    return str(value)


def _get_selected_top_key() -> str:
    selected = _first_query_value(st.query_params.get("top"), "overall")

    if selected not in METRIC_LABELS:
        selected = "overall"

    return selected


def _top_filter_html(selected_key: str) -> str:
    buttons = ""

    for key, label in METRIC_LABELS.items():
        active = " active" if key == selected_key else ""

        buttons += dedent(
            f"""
            <a class="ranking-filter{active}"
               href="?page=coach_dashboard&top={html.escape(key)}"
               target="_self">
               {html.escape(label)}
            </a>
            """
        ).strip()

    return dedent(
        f"""
        <div class="ranking-filter-row">
          {buttons}
        </div>
        """
    ).strip()


def _top_players_list_html(top_players: dict, selected_key: str) -> str:
    rows = top_players.get(selected_key, [])

    if not rows:
        return "<div class='mini-rank-meta'>표시할 선수가 없습니다.</div>"

    rank_rows = "".join(
        _rank_row(idx, row)
        for idx, row in enumerate(rows, start=1)
    )

    return dedent(
        f"""
        <div class="ranking-list">
          {rank_rows}
        </div>
        """
    ).strip()


def _top_players_panel_html(top_players: dict, selected_key: str) -> str:
    return dedent(
        f"""
        <div class="bottom-panel">
          <div class="dashboard-section-title">바르셀로나 TOP 선수</div>
          {_top_filter_html(selected_key)}
          {_top_players_list_html(top_players, selected_key)}
        </div>
        """
    ).strip()


def _score_panel_html(position_scores: list[dict]) -> str:
    return dedent(
        f"""
        <div class="bottom-panel">
          <div class="dashboard-section-title score-title">포지션별 평균 능력치</div>
          {_position_score_html(position_scores)}
        </div>
        """
    ).strip()


def render() -> None:
    st.session_state.current_page = "coach_dashboard"
    st.session_state.user_mode = "coach"


    players = load_barcelona_players()

    if players.empty:
        st.error("바르셀로나 선수 데이터가 비어 있습니다. data/manager_players.csv의 club 컬럼을 확인해 주세요.")
        return

    payload = build_dashboard_payload(players)
    summary = payload["summary"]

    page_title(
        "선수 대시보드",
        "FC Barcelona 선수단의 전력 분포와 포지션별 강점을 확인합니다.",
    )

    top_left, top_right = st.columns([1.55, 0.85], gap="medium")

    with top_left:
        st.markdown(
            _summary_metrics_html(summary),
            unsafe_allow_html=True,
        )

    with top_right:
        st.markdown(
            _position_distribution_html(payload["positionDistribution"]),
            unsafe_allow_html=True,
        )

    st.markdown("<div class='middle-layout-spacer'></div>", unsafe_allow_html=True)

    rank_col, score_col = st.columns([1.05, 1.15], gap="medium")

    selected_top_key = _get_selected_top_key()

    with rank_col:
        st.markdown(
            _top_players_panel_html(payload["topPlayers"], selected_top_key),
            unsafe_allow_html=True,
        )

    with score_col:
        st.markdown(
            _score_panel_html(payload["positionScores"]),
            unsafe_allow_html=True,
        )
