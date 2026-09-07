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


def _top_players_panel_html(top_players: dict) -> str:
    # 브라우저의 기본 라디오 선택으로 목록만 전환한다. 주소 이동이나 rerun은 없다.
    controls = []
    labels = []
    panels = []
    for index, (metric_key, label) in enumerate(METRIC_LABELS.items()):
        control_id = f"dashboard-ranking-{metric_key}"
        checked = " checked" if index == 0 else ""
        controls.append(
            f'<input class="ranking-choice" type="radio" '
            f'name="dashboard-ranking" id="{control_id}" '
            f'aria-controls="{control_id}-panel"{checked}>'
        )
        labels.append(
            f'<label class="ranking-filter" for="{control_id}">{label}</label>'
        )
        panels.append(
            f'<section class="ranking-choice-panel" id="{control_id}-panel" '
            f'aria-label="{label} 선수 랭킹">'
            + _top_players_list_html(top_players, metric_key)
            + '</section>'
        )
    return (
        '<div class="bottom-panel ranking-panel">'
        '<div class="dashboard-section-title">바르셀로나 TOP 선수</div>'
        '<fieldset class="ranking-switcher">'
        '<legend class="ranking-visually-hidden">선수 랭킹 기준</legend>'
        + ''.join(controls)
        + '<div class="ranking-filter-row">' + ''.join(labels) + '</div>'
        + ''.join(panels)
        + '</fieldset></div>'
    )


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

    # 각 행을 하나의 CSS grid로 렌더링해 두 패널이 같은 높이를 공유한다.
    st.markdown(
        '<div class="dashboard-paired-row dashboard-summary-row">'
        + _summary_metrics_html(summary)
        + _position_distribution_html(payload["positionDistribution"])
        + '</div>',
        unsafe_allow_html=True,
    )

    # 라디오를 Markdown의 React 요소로 변환하지 않고 원시 HTML로 렌더링한다.
    # 선택 상태는 브라우저에서 처리하므로 메뉴 클릭 시 Python을 재실행하지 않는다.
    st.html(
        '<div class="dashboard-paired-row dashboard-detail-row">'
        + _top_players_panel_html(payload["topPlayers"])
        + _score_panel_html(payload["positionScores"])
        + '</div>',
    )
