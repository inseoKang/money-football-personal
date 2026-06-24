from __future__ import annotations

import base64
import html
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _image_to_base64_src(image_path: str) -> str:
    if not image_path:
        return ""

    path = Path(str(image_path).strip())

    # CSV 경로가 assets/players/xxx.png 형태일 때 프로젝트 루트 기준으로 찾기
    if not path.is_absolute():
        path = ROOT_DIR / path

    if not path.exists() or not path.is_file():
        return ""

    suffix = path.suffix.lower()

    if suffix in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    else:
        mime = "image/png"

    try:
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""


def player_card_html(player: dict, selected: bool = False) -> str:
    state = "selected" if selected else ""

    score = max(
        _safe_int(player.get("attack_score", 0)),
        _safe_int(player.get("midfield_score", 0)),
        _safe_int(player.get("defense_score", 0)),
        _safe_int(player.get("gk_score", 0)),
    )

    name = html.escape(str(player.get("name", "")))
    position = html.escape(str(player.get("position", "")))
    detail_position = html.escape(str(player.get("detail_position", "")))

    number = _safe_int(player.get("number", 0))
    number_text = str(number) if number else "-"

    image_path = str(player.get("image_path", "")).strip()
    image_src = _image_to_base64_src(image_path)

    if image_src:
        avatar = (
            f'<div class="avatar player-photo-wrap">'
            f'<img class="player-photo" src="{image_src}" alt="{name}">'
            f'</div>'
        )
    else:
        avatar = f'<div class="avatar">{number_text}</div>'

    selected_badge = "<div class='selected-pill'>선택됨</div>" if selected else ""

    return f"""
    <div class="player-card {state}">
      <div class="drag-dot">⋮⋮</div>
      {avatar}
      <div class="player-main">
        <div class="player-title">#{number_text} {name} <span>{position}</span></div>
        <div class="player-sub">{detail_position} · 적합도 {score}</div>
      </div>
      <div class="score-pill">{score}</div>
      {selected_badge}
    </div>
    """


def stat_card_html(title: str, value: str | int, caption: str = "") -> str:
    return f"""
    <div class="stat-card">
      <div class="stat-title">{html.escape(str(title))}</div>
      <div class="stat-value">{html.escape(str(value))}</div>
      <div class="stat-caption">{html.escape(str(caption))}</div>
    </div>
    """

def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def manager_player_card_html(player: dict, selected: bool = False) -> str:
    """src.coach.lineup_payload._player_payload() 구조를 표시하는 감독용 선수 카드입니다."""
    state = "selected" if selected else ""

    salary_id = html.escape(str(player.get("salaryId", "-")))
    name = html.escape(str(player.get("name", "-")))
    club = html.escape(str(player.get("club", "-")))
    league = html.escape(str(player.get("league", "-")))
    position = html.escape(str(player.get("positionGroup", "-")))
    age = html.escape(str(player.get("age", "-")))

    scores = player.get("scores", {}) or {}
    stats = player.get("stats", {}) or {}

    overall = _safe_float(scores.get("overall", 0))
    goals = html.escape(str(stats.get("goals", 0)))
    assists = html.escape(str(stats.get("assists", 0)))
    minutes = html.escape(str(stats.get("minutes", 0)))

    selected_badge = "<div class='selected-pill'>선택됨</div>" if selected else ""

    return f"""
    <div class="player-card {state}">
      <div class="drag-dot">⋮⋮</div>
      <div class="avatar">{position}</div>
      <div class="player-main">
        <div class="player-title">{name} <span>#{salary_id}</span></div>
        <div class="player-sub">{club} · {league} · {age}세</div>
        <div class="player-sub">득점 {goals} · 도움 {assists} · 출전 {minutes}분</div>
      </div>
      <div class="score-pill">{overall:.0f}</div>
      {selected_badge}
    </div>
    """


def top_player_card_html(player: dict, rank: int, label: str = "점수") -> str:
    name = html.escape(str(player.get("player", "-")))
    club = html.escape(str(player.get("club", "-")))
    league = html.escape(str(player.get("league", "-")))
    position = html.escape(str(player.get("position", "-")))
    value = _safe_float(player.get("value", 0))
    overall = _safe_float(player.get("overall", 0))
    value_label = html.escape(str(label))

    return f"""
    <div class="player-card">
      <div class="avatar">{rank}</div>
      <div class="player-main">
        <div class="player-title">{name} <span>{position}</span></div>
        <div class="player-sub">{club} · {league}</div>
        <div class="player-sub">종합 {overall:.1f}</div>
      </div>
      <div class="score-pill" title="{value_label}">{value:.0f}</div>
    </div>
    """
