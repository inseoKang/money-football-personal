"""Similar player search for scout Button 3."""

from __future__ import annotations

import csv
import io
import math
from pathlib import Path

from src.scout.azure_blob_loader import ScoutBlobLoader, scout_blob_paths
from src.scout.scout_features import parse_float


SIMILARITY_FOCUS_OPTIONS = [
    {"value": "overall", "label": "전체 스타일", "description": "역할, 공격, 수비, 연봉 효율을 함께 비교합니다."},
    {"value": "role", "label": "역할 적합도", "description": "사전에 계산한 역할별 적합도 점수를 비교합니다."},
    {"value": "attack", "label": "공격 성향", "description": "공격, 슈팅, 찬스 창출 점수를 비교합니다."},
    {"value": "passing", "label": "창의/전개 성향", "description": "패스 원천 데이터가 제한되어 proxy 점수를 사용합니다."},
    {"value": "defense", "label": "수비 성향", "description": "수비 액션, 볼 회수, 공중볼 수비 점수를 비교합니다."},
    {"value": "physical", "label": "활동량/압박", "description": "압박, 공중볼, 출전 시간 percentile을 비교합니다."},
    {"value": "value", "label": "가성비 대체 후보", "description": "성능과 연봉 가치 점수를 함께 비교합니다."},
]

POSITION_SCOPE_OPTIONS = [
    {"value": "same_position", "label": "같은 포지션", "description": "기준 선수와 같은 포지션 그룹만 봅니다."},
    {"value": "adjacent_position", "label": "인접 포지션", "description": "전술적으로 가까운 포지션 그룹까지 허용합니다."},
    {"value": "all", "label": "전체 포지션", "description": "모든 포지션 그룹에서 후보를 찾습니다."},
]

FOCUS_COLUMNS = {
    "overall": [
        "overall_role_score",
        "attack_score",
        "shooting_score",
        "chance_creation_score",
        "pressing_score",
        "defensive_action_score",
        "salary_efficiency_score",
    ],
    "role": [
        "role_fit_finisher",
        "role_fit_pressing_forward",
        "role_fit_creative_midfielder",
        "role_fit_progressive_passer",
        "role_fit_ball_winning_midfielder",
        "role_fit_ball_playing_defender",
        "role_fit_defensive_stopper",
        "role_fit_shot_stopper",
    ],
    "attack": ["attack_score", "shooting_score", "chance_creation_score"],
    "passing": ["chance_creation_score", "creative_pass_score", "progressive_pass_score", "build_up_score"],
    "defense": ["defensive_action_score", "ball_winning_score", "aerial_defense_score"],
    "physical": ["pressing_score", "aerial_defense_score", "minutes_percentile_by_position"],
    "value": [
        "overall_role_score",
        "salary_efficiency_score",
        "salary_value_score",
        "performance_percentile_by_position",
        "salary_percentile_by_position",
    ],
}

ADJACENT_POSITION_GROUPS = {
    "FW": {"FW", "MF"},
    "MF": {"FW", "MF", "DF"},
    "DF": {"MF", "DF", "GK"},
    "GK": {"GK", "DF"},
}


def get_similarity_focus_options() -> list[dict[str, str]]:
    """Return frontend options for the Button 3 similarity focus."""
    return [dict(option) for option in SIMILARITY_FOCUS_OPTIONS]


def get_position_scope_options() -> list[dict[str, str]]:
    """Return frontend options for Button 3 position scope."""
    return [dict(option) for option in POSITION_SCOPE_OPTIONS]


def load_backend_players_from_blob(loader: ScoutBlobLoader | None = None) -> list[dict[str, str]]:
    """Load the scout backend dataset from Azure Blob Storage."""
    blob_loader = loader or ScoutBlobLoader()
    text = blob_loader.download_text(scout_blob_paths()["backend_dataset"])
    return list(csv.DictReader(io.StringIO(text)))


def load_backend_players_from_csv(path: str | Path) -> list[dict[str, str]]:
    """Load scout backend rows from a local CSV path."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_player_feature_vector(player: dict[str, str], focus: str = "overall") -> dict[str, float]:
    """Build a numeric similarity vector for one player."""
    columns = FOCUS_COLUMNS.get(focus, FOCUS_COLUMNS["overall"])
    return {column: parse_float(player.get(column)) if parse_float(player.get(column)) is not None else 50.0 for column in columns}


def calculate_similarity_score(
    base_vector: dict[str, float],
    candidate_vector: dict[str, float],
    focus: str = "overall",
) -> float:
    """Return a 0-100 weighted distance similarity score."""
    columns = FOCUS_COLUMNS.get(focus, FOCUS_COLUMNS["overall"])
    if not columns:
        return 0.0
    squared_distance = 0.0
    for column in columns:
        base_value = float(base_vector.get(column, 50.0))
        candidate_value = float(candidate_vector.get(column, 50.0))
        squared_distance += (base_value - candidate_value) ** 2
    distance = math.sqrt(squared_distance / len(columns))
    return round(max(0.0, 100.0 - distance), 2)


def find_similar_players(
    filters: dict,
    players: list[dict[str, str]] | None = None,
    view_path: str | Path | None = None,
) -> list[dict[str, object]]:
    """Find similar players for Button 3.

    Defaults:
    - similarity_focus: overall
    - position_scope: same_position
    - league: ALL
    - min_minutes: 700
    - top_n: 20
    """
    rows = players if players is not None else _load_default_players(view_path)
    base_player_id = str(filters.get("base_player_id") or "")
    if not base_player_id:
        raise ValueError("base_player_id is required")

    base_player = _find_by_player_id(rows, base_player_id)
    focus = str(filters.get("similarity_focus") or "overall")
    if focus not in FOCUS_COLUMNS:
        focus = "overall"
    position_scope = str(filters.get("position_scope") or "same_position")
    league = str(filters.get("league") or "ALL")
    age_max = parse_float(filters.get("age_max"))
    max_salary = parse_float(filters.get("max_salary"))
    min_minutes = parse_float(filters.get("min_minutes"))
    if min_minutes is None:
        min_minutes = 700.0
    top_n = max(1, min(int(filters.get("top_n") or 20), 100))

    base_vector = build_player_feature_vector(base_player, focus)
    candidates: list[dict[str, object]] = []

    for row in rows:
        if row.get("player_id") == base_player_id:
            continue
        if not _position_allowed(base_player.get("position_group", ""), row.get("position_group", ""), position_scope):
            continue
        if league != "ALL" and row.get("league") != league:
            continue
        if not _range_allowed(row.get("age"), None, age_max):
            continue
        if not _range_allowed(row.get("salary_annual_gross_eur"), None, max_salary):
            continue
        if not _range_allowed(row.get("minutes"), min_minutes, None):
            continue

        candidate_vector = build_player_feature_vector(row, focus)
        score = calculate_similarity_score(base_vector, candidate_vector, focus)
        candidates.append(_build_similarity_result(row, base_player, score, focus))

    candidates.sort(key=lambda item: (float(item["similarity_score"]), float(item.get("minutes") or 0)), reverse=True)
    return candidates[:top_n]


def _load_default_players(view_path: str | Path | None) -> list[dict[str, str]]:
    if view_path:
        return load_backend_players_from_csv(view_path)
    return load_backend_players_from_blob()


def _find_by_player_id(rows: list[dict[str, str]], player_id: str) -> dict[str, str]:
    for row in rows:
        if row.get("player_id") == player_id:
            return row
    raise ValueError(f"base_player_id not found: {player_id}")


def _position_allowed(base_group: str, candidate_group: str, scope: str) -> bool:
    if scope == "all":
        return True
    if scope == "adjacent_position":
        return candidate_group in ADJACENT_POSITION_GROUPS.get(base_group, {base_group})
    return candidate_group == base_group


def _range_allowed(value: object, minimum: float | None, maximum: float | None) -> bool:
    number = parse_float(value)
    if number is None:
        return False
    if minimum is not None and number < minimum:
        return False
    if maximum is not None and number > maximum:
        return False
    return True


def _build_similarity_result(
    row: dict[str, str],
    base_player: dict[str, str],
    score: float,
    focus: str,
) -> dict[str, object]:
    return {
        "player_id": row.get("player_id", ""),
        "player_name": row.get("player_name", ""),
        "team": row.get("team", ""),
        "league": row.get("league", ""),
        "position_group": row.get("position_group", ""),
        "age": _number(row.get("age")),
        "minutes": _number(row.get("minutes")),
        "salary_annual_gross_eur": _number(row.get("salary_annual_gross_eur")),
        "similarity_score": score,
        "similarity_label": _similarity_label(score),
        "similarity_focus": focus,
        "base_player_name": base_player.get("player_name", ""),
        "salary_value_label": row.get("salary_value_label", ""),
        "salary_value_score": _number(row.get("salary_value_score")),
        "similarity_reason_summary": _similarity_reason(focus, score),
        "data_quality_note": row.get("data_quality_note", ""),
    }


def _similarity_label(score: float) -> str:
    if score >= 85:
        return "매우 유사"
    if score >= 70:
        return "유사"
    if score >= 55:
        return "부분 유사"
    return "낮은 유사도"


def _similarity_reason(focus: str, score: float) -> str:
    focus_label = next((option["label"] for option in SIMILARITY_FOCUS_OPTIONS if option["value"] == focus), "전체 스타일")
    return f"{focus_label} 기준 점수 분포를 비교해 {score:.1f}/100 유사도로 계산했습니다."


def _number(value: object) -> float | int | None:
    parsed = parse_float(value)
    if parsed is None:
        return None
    return int(parsed) if float(parsed).is_integer() else parsed
