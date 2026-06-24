from __future__ import annotations

import html
import math

import streamlit as st
import streamlit.components.v1 as components


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _clamp_score(value) -> float:
    return max(0, min(100, _safe_float(value)))


def _radar_points(values: list[float], cx: int = 130, cy: int = 130, radius: int = 82) -> str:
    points = []

    for index, value in enumerate(values):
        angle = -math.pi / 2 + (2 * math.pi * index / len(values))
        ratio = _clamp_score(value) / 100
        x = cx + math.cos(angle) * radius * ratio
        y = cy + math.sin(angle) * radius * ratio
        points.append(f"{x:.1f},{y:.1f}")

    return " ".join(points)


def _outer_points(count: int = 6, cx: int = 130, cy: int = 130, radius: int = 82) -> str:
    points = []

    for index in range(count):
        angle = -math.pi / 2 + (2 * math.pi * index / count)
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        points.append(f"{x:.1f},{y:.1f}")

    return " ".join(points)


def _score_bar(label: str, value) -> str:
    score = _clamp_score(value)

    return f"""
    <div class="score-row">
      <div class="score-label">
        <span>{html.escape(label)}</span>
        <b>{score:.0f}</b>
      </div>
      <div class="score-track">
        <div class="score-fill" style="width:{score}%"></div>
      </div>
    </div>
    """


def _stat_box(label: str, value) -> str:
    return f"""
    <div class="stat-box">
      <span>{html.escape(str(label))}</span>
      <strong>{html.escape(str(value))}</strong>
    </div>
    """


def _build_detail_html(player: dict) -> str:
    scores = player.get("scores", {}) or {}
    stats = player.get("stats", {}) or {}

    name = html.escape(str(player.get("name", "-")))
    club = html.escape(str(player.get("club", "-")))
    league = html.escape(str(player.get("league", "-")))
    position = html.escape(str(player.get("positionGroup", "-")))
    age = html.escape(str(player.get("age", "-")))
    country = html.escape(str(player.get("country", "-")))
    salary_id = html.escape(str(player.get("salaryId", "-")))

    overall = _clamp_score(scores.get("overall", 0))
    attack = _clamp_score(scores.get("attack", 0))
    defense = _clamp_score(scores.get("defense", 0))
    keeper = _clamp_score(scores.get("keeper", 0))
    stamina = _clamp_score(scores.get("stamina", 0))
    discipline = _clamp_score(scores.get("discipline", 0))

    radar_values = [attack, defense, keeper, stamina, discipline, overall]

    radar_polygon = _radar_points(radar_values)
    outer_polygon = _outer_points()

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>
  * {{
    box-sizing: border-box;
  }}

  body {{
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #e8f6ff;
  }}

  .detail-wrap {{
    background: #0b1b29;
    border-radius: 18px;
    padding: 18px;
  }}

  .detail-head {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 18px;
    border-radius: 18px;
    background: linear-gradient(135deg, #102638, #19384d);
    border: 1px solid rgba(143, 176, 195, .25);
    margin-bottom: 14px;
  }}

  .name {{
    font-size: 24px;
    font-weight: 900;
    margin-bottom: 8px;
  }}

  .sub {{
    color: #9bb9cb;
    font-size: 13px;
    font-weight: 700;
  }}

  .overall {{
    width: 92px;
    height: 92px;
    border-radius: 22px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(32, 217, 135, .14);
    border: 1px solid rgba(32, 217, 135, .55);
  }}

  .overall strong {{
    color: #dffff4;
    font-size: 32px;
    line-height: 1;
  }}

  .overall span {{
    color: #8fb0c3;
    font-size: 10px;
    font-weight: 900;
    margin-top: 6px;
  }}

  .grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }}

  .panel {{
    border-radius: 18px;
    background: #132b3b;
    border: 1px solid rgba(143, 176, 195, .24);
    padding: 18px;
    min-height: 430px;
  }}

  .panel-title {{
    font-size: 16px;
    font-weight: 900;
    margin-bottom: 14px;
  }}

  .radar-area {{
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
  }}

  svg {{
    width: 260px;
    height: 260px;
  }}

  .grid-poly {{
    fill: rgba(255,255,255,.025);
    stroke: rgba(143,176,195,.35);
    stroke-width: 1.4;
  }}

  .grid-small {{
    fill: none;
    stroke: rgba(143,176,195,.18);
    stroke-width: 1;
  }}

  .axis {{
    stroke: rgba(143,176,195,.22);
    stroke-width: 1;
  }}

  .radar-score {{
    fill: rgba(32, 217, 135, .25);
    stroke: #20d987;
    stroke-width: 3;
  }}

  .radar-dot {{
    fill: #20d987;
  }}

  .radar-label {{
    fill: #dff7ff;
    font-size: 11px;
    font-weight: 900;
  }}

  .score-row {{
    margin-top: 11px;
  }}

  .score-label {{
    display: flex;
    justify-content: space-between;
    color: #dff7ff;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 5px;
  }}

  .score-label b {{
    color: #20d987;
  }}

  .score-track {{
    height: 8px;
    border-radius: 999px;
    background: rgba(143,176,195,.18);
    overflow: hidden;
  }}

  .score-fill {{
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #20d987, #22d3ee);
  }}

  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }}

  .stat-box {{
    padding: 14px;
    border-radius: 14px;
    background: rgba(255,255,255,.045);
    border: 1px solid rgba(143,176,195,.2);
  }}

  .stat-box span {{
    display: block;
    color: #8fb0c3;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 8px;
  }}

  .stat-box strong {{
    color: #e8f6ff;
    font-size: 17px;
    font-weight: 900;
  }}

  .note {{
    margin-top: 14px;
    padding: 14px;
    border-radius: 14px;
    background: rgba(32, 217, 135, .08);
    border: 1px solid rgba(32, 217, 135, .24);
    color: #a8c5d4;
    font-size: 12px;
    line-height: 1.55;
    font-weight: 700;
  }}
</style>
</head>
<body>
  <div class="detail-wrap">
    <div class="detail-head">
      <div>
        <div class="name">{name}</div>
        <div class="sub">#{salary_id} · {club} · {league} · {position} · {age}세 · {country}</div>
      </div>
      <div class="overall">
        <strong>{overall:.0f}</strong>
        <span>OVERALL</span>
      </div>
    </div>

    <div class="grid">
      <div class="panel">
        <div class="panel-title">선수 능력치 Radar</div>

        <div class="radar-area">
          <svg viewBox="0 0 260 260">
            <polygon class="grid-poly" points="{outer_polygon}" />
            <polygon class="grid-small" points="{_radar_points([75, 75, 75, 75, 75, 75])}" />
            <polygon class="grid-small" points="{_radar_points([50, 50, 50, 50, 50, 50])}" />
            <polygon class="grid-small" points="{_radar_points([25, 25, 25, 25, 25, 25])}" />

            <line class="axis" x1="130" y1="130" x2="130" y2="48" />
            <line class="axis" x1="130" y1="130" x2="201" y2="89" />
            <line class="axis" x1="130" y1="130" x2="201" y2="171" />
            <line class="axis" x1="130" y1="130" x2="130" y2="212" />
            <line class="axis" x1="130" y1="130" x2="59" y2="171" />
            <line class="axis" x1="130" y1="130" x2="59" y2="89" />

            <polygon class="radar-score" points="{radar_polygon}" />

            <text class="radar-label" x="130" y="24" text-anchor="middle">공격</text>
            <text class="radar-label" x="226" y="81" text-anchor="middle">수비</text>
            <text class="radar-label" x="226" y="183" text-anchor="middle">GK</text>
            <text class="radar-label" x="130" y="244" text-anchor="middle">체력</text>
            <text class="radar-label" x="34" y="183" text-anchor="middle">규율</text>
            <text class="radar-label" x="34" y="81" text-anchor="middle">종합</text>
          </svg>
        </div>

        {_score_bar("공격 점수", attack)}
        {_score_bar("수비 점수", defense)}
        {_score_bar("골키퍼 점수", keeper)}
        {_score_bar("체력 점수", stamina)}
        {_score_bar("규율 점수", discipline)}
      </div>

      <div class="panel">
        <div class="panel-title">주요 기록</div>

        <div class="stat-grid">
          {_stat_box("출전", stats.get("matches", 0))}
          {_stat_box("출전 시간", f"{_safe_int(stats.get('minutes', 0)):,}분")}
          {_stat_box("득점", stats.get("goals", 0))}
          {_stat_box("도움", stats.get("assists", 0))}
          {_stat_box("공격 점수", f"{attack:.1f}")}
          {_stat_box("수비 점수", f"{defense:.1f}")}
          {_stat_box("체력 점수", f"{stamina:.1f}")}
          {_stat_box("규율 점수", f"{discipline:.1f}")}
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""


@st.dialog("선수 상세 정보", width="large")
def show_player_detail_dialog(player: dict) -> None:
    components.html(
        _build_detail_html(player),
        height=720,
        scrolling=True,
    )