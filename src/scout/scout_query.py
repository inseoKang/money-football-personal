"""Query helpers for scout search buttons."""

from __future__ import annotations

from pathlib import Path

from src.scout.scout_features import DEFAULT_VIEW_PATH, parse_bool, parse_float, read_csv_rows
from src.scout.similarity import (
    POSITION_SCOPE_OPTIONS,
    SIMILARITY_FOCUS_OPTIONS,
    build_player_feature_vector,
    calculate_similarity_score,
    find_similar_players,
)


ROLE_SCORE_COLUMNS = {
    "Finisher": "role_fit_finisher",
    "Pressing Forward": "role_fit_pressing_forward",
    "Creative Midfielder": "role_fit_creative_midfielder",
    "Progressive Passer": "role_fit_progressive_passer",
    "Ball Winning Midfielder": "role_fit_ball_winning_midfielder",
    "Ball Playing Defender": "role_fit_ball_playing_defender",
    "Defensive Stopper": "role_fit_defensive_stopper",
    "Shot Stopper": "role_fit_shot_stopper",
}

POSITION_ROLE_OPTIONS = {
    "ALL": list(ROLE_SCORE_COLUMNS),
    "FW": ["Finisher", "Pressing Forward"],
    "MF": ["Creative Midfielder", "Progressive Passer", "Ball Winning Midfielder"],
    "DF": ["Ball Playing Defender", "Defensive Stopper"],
    "GK": ["Shot Stopper"],
}

TACTICAL_NEED_OPTIONS = {
    "Finisher": ["박스 안 득점력이 필요함", "슈팅 효율이 좋은 공격수가 필요함"],
    "Pressing Forward": ["높은 압박과 활동량이 필요함", "전방 수비 가담이 필요함"],
    "Creative Midfielder": ["찬스 메이킹과 전진 패스가 필요함", "공간을 창출하는 패스가 필요함"],
    "Progressive Passer": ["전진 패스와 빌드업 안정성이 필요함", "중원에서 볼을 앞으로 운반할 선수가 필요함"],
    "Ball Winning Midfielder": ["중원 압박과 볼 탈취가 필요함", "수비 전환에서 공을 끊어줄 선수가 필요함"],
    "Ball Playing Defender": ["후방 빌드업 안정성이 필요함", "수비수가 전진 패스를 공급해야 함"],
    "Defensive Stopper": ["공중볼과 수비 안정성이 필요함", "상대 공격수를 강하게 막아줄 선수가 필요함"],
    "Shot Stopper": ["골문 안정성과 출전 경험이 필요함"],
}

PRIORITY_METRIC_SCORE_COLUMNS = {
    "공격": "attack_score",
    "슈팅": "shooting_score",
    "찬스 창출": "chance_creation_score",
    "전진 패스": "progressive_pass_score",
    "창의 패스": "creative_pass_score",
    "압박": "pressing_score",
    "수비": "defensive_action_score",
    "볼 탈취": "ball_winning_score",
    "빌드업": "build_up_score",
    "공중볼/수비": "aerial_defense_score",
    "GK": "goalkeeper_score",
    "패스": "creative_pass_score",
    "중원 전개": "progressive_pass_score",
    "피지컬": "aerial_defense_score",
}

ADVANCED_SCORE_FILTER_COLUMNS = {
    "overall_role_score_min": "overall_role_score",
    "attack_score_min": "attack_score",
    "shooting_score_min": "shooting_score",
    "chance_creation_score_min": "chance_creation_score",
    "progressive_pass_score_min": "progressive_pass_score",
    "creative_pass_score_min": "creative_pass_score",
    "pressing_score_min": "pressing_score",
    "defensive_action_score_min": "defensive_action_score",
    "ball_winning_score_min": "ball_winning_score",
    "build_up_score_min": "build_up_score",
    "aerial_defense_score_min": "aerial_defense_score",
    "goalkeeper_score_min": "goalkeeper_score",
    "salary_value_score_min": "salary_value_score",
    "salary_efficiency_score_min": "salary_efficiency_score",
    "role_fit_finisher_min": "role_fit_finisher",
    "role_fit_pressing_forward_min": "role_fit_pressing_forward",
    "role_fit_creative_midfielder_min": "role_fit_creative_midfielder",
    "role_fit_progressive_passer_min": "role_fit_progressive_passer",
    "role_fit_ball_winning_midfielder_min": "role_fit_ball_winning_midfielder",
    "role_fit_ball_playing_defender_min": "role_fit_ball_playing_defender",
    "role_fit_defensive_stopper_min": "role_fit_defensive_stopper",
    "role_fit_shot_stopper_min": "role_fit_shot_stopper",
}

ADVANCED_SORT_COLUMNS = {
    "overall_role_score": "overall_role_score",
    "salary_value_score": "salary_value_score",
    "salary_efficiency_score": "salary_efficiency_score",
    "attack_score": "attack_score",
    "shooting_score": "shooting_score",
    "chance_creation_score": "chance_creation_score",
    "progressive_pass_score": "progressive_pass_score",
    "creative_pass_score": "creative_pass_score",
    "pressing_score": "pressing_score",
    "defensive_action_score": "defensive_action_score",
    "ball_winning_score": "ball_winning_score",
    "build_up_score": "build_up_score",
    "aerial_defense_score": "aerial_defense_score",
    "goalkeeper_score": "goalkeeper_score",
    "minutes": "minutes",
    "age": "age",
    "salary_annual_gross_eur": "salary_annual_gross_eur",
    **{column: column for column in ROLE_SCORE_COLUMNS.values()},
}

ADVANCED_RESULT_FIELDS = [
    "player_id",
    "player_name",
    "team",
    "league",
    "position_group",
    "age",
    "minutes",
    "salary_annual_gross_eur",
    "overall_role_score",
    "salary_value_label",
    "salary_value_score",
    "salary_efficiency_score",
    "data_quality_note",
]


def get_role_options(position_group: str | None = None) -> list[dict[str, str]]:
    """Return role options allowed for the selected position group."""
    group = (position_group or "ALL").upper()
    roles = POSITION_ROLE_OPTIONS.get(group, POSITION_ROLE_OPTIONS["ALL"])
    return [{"value": role, "label": role, "score_column": ROLE_SCORE_COLUMNS[role]} for role in roles]


def get_tactical_need_options(role_key: str | None = None) -> list[dict[str, str]]:
    """Return tactical need options for a role."""
    role = role_key or "Creative Midfielder"
    options = TACTICAL_NEED_OPTIONS.get(role, [])
    return [{"value": option, "label": option} for option in options]


def get_similarity_focus_options() -> list[dict[str, str]]:
    """Return similarity focus options for Button 3."""
    return [dict(option) for option in SIMILARITY_FOCUS_OPTIONS]


def get_position_scope_options() -> list[dict[str, str]]:
    """Return position scope options for Button 3."""
    return [dict(option) for option in POSITION_SCOPE_OPTIONS]


def load_scout_player_view(path: str | Path = DEFAULT_VIEW_PATH) -> list[dict[str, str]]:
    """Load the processed scout player view."""
    return read_csv_rows(path)


def get_player_search_options(keyword: str, limit: int = 20) -> list[dict[str, object]]:
    """Return player autocomplete options for Button 2 from Azure Blob assets."""
    from src.scout.salary_value import get_salary_value_service

    return get_salary_value_service().get_player_search_options(keyword, limit=limit)


def evaluate_player_value(
    player_id: str | None = None,
    player_name: str | None = None,
    include_shap: bool = True,
    top_features: int = 5,
) -> dict[str, object]:
    """Evaluate one player's salary value for Button 2 using Blob model assets."""
    from src.scout.salary_value import get_salary_value_service

    return get_salary_value_service().evaluate_player_value(
        player_id=player_id,
        player_name=player_name,
        include_shap=include_shap,
        top_features=top_features,
    )


def get_advanced_filter_schema(
    players: list[dict[str, str]] | None = None,
    view_path: str | Path = DEFAULT_VIEW_PATH,
) -> dict[str, object]:
    """Return the allowed filter schema for Button 4 advanced search."""
    rows = players if players is not None else load_scout_player_view(view_path)
    leagues = sorted({row.get("league", "") for row in rows if row.get("league")})
    teams = sorted({row.get("team", "") for row in rows if row.get("team")})
    salary_statuses = sorted({row.get("salary_value_status", "") for row in rows if row.get("salary_value_status")})

    score_filters = [
        {"key": key, "column": column, "type": "slider", "min": 0, "max": 100, "default": None}
        for key, column in ADVANCED_SCORE_FILTER_COLUMNS.items()
    ]

    return {
        "position_group": {
            "type": "select",
            "label": "포지션 그룹",
            "options": ["ALL", "FW", "MF", "DF", "GK"],
            "default": "ALL",
        },
        "league": {"type": "select", "label": "리그", "options": ["ALL", *leagues], "default": "ALL"},
        "team": {"type": "select", "label": "팀", "options": ["ALL", *teams], "default": "ALL"},
        "age": {"type": "range", "label": "나이", "min_key": "age_min", "max_key": "age_max"},
        "salary": {
            "type": "range",
            "label": "연봉",
            "min_key": "salary_min",
            "max_key": "salary_max",
            "unit": "EUR",
        },
        "minutes_min": {"type": "number", "label": "최소 출전 시간", "default": 700},
        "salary_available_only": {"type": "checkbox", "label": "연봉 확인 선수만", "default": False},
        "score_available_only": {"type": "checkbox", "label": "점수 계산 가능 선수만", "default": True},
        "salary_value_status": {
            "type": "select",
            "label": "연봉 가치 상태",
            "options": ["ALL", *salary_statuses],
            "default": "ALL",
        },
        "score_filters": score_filters,
        "sort_by": {
            "type": "select",
            "label": "정렬 기준",
            "options": list(ADVANCED_SORT_COLUMNS),
            "default": "overall_role_score",
        },
        "sort_direction": {
            "type": "select",
            "label": "정렬 방향",
            "options": ["desc", "asc"],
            "default": "desc",
        },
        "top_n": {"type": "number", "label": "결과 개수", "min": 1, "max": 100, "default": 50},
    }


def _matches_number_range(value: str | None, minimum: float | None = None, maximum: float | None = None) -> bool:
    number = parse_float(value)
    if number is None:
        return False
    if minimum is not None and number < minimum:
        return False
    if maximum is not None and number > maximum:
        return False
    return True


def _priority_adjusted_score(row: dict[str, str], base_score_column: str, priority_metrics: list[str] | None) -> float:
    base_score = parse_float(row.get(base_score_column)) or 0.0
    if not priority_metrics:
        return round(base_score, 2)

    priority_columns = [
        score_column
        for metric in priority_metrics
        if (score_column := PRIORITY_METRIC_SCORE_COLUMNS.get(metric))
    ]
    if not priority_columns:
        return round(base_score, 2)

    priority_scores = [parse_float(row.get(column)) for column in priority_columns]
    valid_priority_scores = [score for score in priority_scores if score is not None]
    if not valid_priority_scores:
        return round(base_score, 2)

    priority_average = sum(valid_priority_scores) / len(valid_priority_scores)
    return round((base_score * 0.85) + (priority_average * 0.15), 2)


def find_role_based_players(
    filters: dict,
    players: list[dict[str, str]] | None = None,
    view_path: str | Path = DEFAULT_VIEW_PATH,
) -> list[dict[str, object]]:
    """Filter and rank players for Button 1, '내가 원하는 선수 찾기'."""
    rows = players if players is not None else load_scout_player_view(view_path)
    role_key = filters.get("role_key") or "Creative Midfielder"
    score_column = ROLE_SCORE_COLUMNS.get(str(role_key), "role_fit_creative_midfielder")
    position_group = str(filters.get("position_group") or "ALL").upper()
    league = str(filters.get("league") or "ALL")
    priority_metrics = filters.get("priority_metrics") or []
    top_n = int(filters.get("top_n") or 20)

    age_min = parse_float(filters.get("age_min"))
    age_max = parse_float(filters.get("age_max"))
    max_salary = parse_float(filters.get("max_salary"))
    min_minutes = parse_float(filters.get("min_minutes"))
    include_loan = bool(filters.get("include_loan", True))
    only_active_salary = bool(filters.get("only_active_salary", False))

    results: list[dict[str, object]] = []
    for row in rows:
        if row.get("score_available") != "true":
            continue
        if position_group != "ALL" and row.get("position_group") != position_group:
            continue
        if league != "ALL" and row.get("league") != league:
            continue
        if age_min is not None or age_max is not None:
            if not _matches_number_range(row.get("age"), age_min, age_max):
                continue
        if min_minutes is not None and not _matches_number_range(row.get("minutes"), min_minutes, None):
            continue
        if max_salary is not None:
            if row.get("salary_available") != "true":
                continue
            if not _matches_number_range(row.get("salary_annual_gross_eur"), None, max_salary):
                continue
        if not include_loan and parse_bool(row.get("salary_loan")) is True:
            continue
        if only_active_salary and parse_bool(row.get("salary_active")) is not True:
            continue

        adjusted_score = _priority_adjusted_score(row, score_column, priority_metrics)
        result = dict(row)
        result["selected_role"] = role_key
        result["selected_score_column"] = score_column
        result["result_score"] = adjusted_score
        results.append(result)

    results.sort(
        key=lambda row: (
            parse_float(row.get("result_score")) or 0.0,
            parse_float(row.get("minutes")) or 0.0,
        ),
        reverse=True,
    )
    return results[:top_n]


def validate_advanced_filters(filters: dict) -> dict[str, object]:
    """Normalize Button 4 filter values into the allowed backend range."""
    values = filters or {}
    warnings: list[str] = []

    position_group = str(values.get("position_group") or "ALL").upper()
    if position_group not in {"ALL", "FW", "MF", "DF", "GK"}:
        warnings.append("invalid_position_group_defaulted")
        position_group = "ALL"

    league = str(values.get("league") or "ALL")
    team = str(values.get("team") or "ALL")
    salary_value_status = str(values.get("salary_value_status") or "ALL")

    sort_by = str(values.get("sort_by") or "overall_role_score")
    if sort_by not in ADVANCED_SORT_COLUMNS:
        warnings.append("invalid_sort_by_defaulted")
        sort_by = "overall_role_score"

    sort_direction = str(values.get("sort_direction") or "desc").lower()
    if sort_direction not in {"asc", "desc"}:
        warnings.append("invalid_sort_direction_defaulted")
        sort_direction = "desc"

    top_n = _parse_int(values.get("top_n"), 50)
    if top_n < 1:
        warnings.append("top_n_min_clamped")
        top_n = 1
    if top_n > 100:
        warnings.append("top_n_max_clamped")
        top_n = 100

    normalized: dict[str, object] = {
        "position_group": position_group,
        "league": league,
        "team": team,
        "age_min": parse_float(values.get("age_min")),
        "age_max": parse_float(values.get("age_max")),
        "salary_min": parse_float(values.get("salary_min")),
        "salary_max": parse_float(values.get("salary_max")),
        "minutes_min": parse_float(values.get("minutes_min")),
        "salary_available_only": _parse_bool_option(values.get("salary_available_only"), False),
        "score_available_only": _parse_bool_option(values.get("score_available_only"), True),
        "salary_value_status": salary_value_status,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
        "top_n": top_n,
        "_warnings": warnings,
    }

    if normalized["minutes_min"] is None:
        normalized["minutes_min"] = 700.0

    if _range_is_reversed(normalized["age_min"], normalized["age_max"]):
        normalized["age_min"], normalized["age_max"] = normalized["age_max"], normalized["age_min"]
        warnings.append("age_range_swapped")
    if _range_is_reversed(normalized["salary_min"], normalized["salary_max"]):
        normalized["salary_min"], normalized["salary_max"] = normalized["salary_max"], normalized["salary_min"]
        warnings.append("salary_range_swapped")

    for filter_key in ADVANCED_SCORE_FILTER_COLUMNS:
        score_min = parse_float(values.get(filter_key))
        if score_min is None:
            continue
        normalized[filter_key] = max(0.0, min(score_min, 100.0))

    return normalized


def apply_advanced_filters(
    filters: dict,
    players: list[dict[str, str]] | None = None,
    view_path: str | Path = DEFAULT_VIEW_PATH,
) -> list[dict[str, str]]:
    """Apply Button 4 advanced filters and return matching raw player rows."""
    rows = players if players is not None else load_scout_player_view(view_path)
    normalized = validate_advanced_filters(filters)

    position_group = str(normalized["position_group"])
    league = str(normalized["league"])
    team = str(normalized["team"])
    salary_value_status = str(normalized["salary_value_status"])

    results: list[dict[str, str]] = []
    for row in rows:
        if normalized["score_available_only"] and row.get("score_available") != "true":
            continue
        if normalized["salary_available_only"] and row.get("salary_available") != "true":
            continue
        if position_group != "ALL" and row.get("position_group") != position_group:
            continue
        if league != "ALL" and row.get("league") != league:
            continue
        if team != "ALL" and row.get("team") != team:
            continue
        if salary_value_status != "ALL" and row.get("salary_value_status") != salary_value_status:
            continue
        if not _matches_optional_range(row.get("age"), normalized["age_min"], normalized["age_max"]):
            continue
        if not _matches_optional_range(row.get("salary_annual_gross_eur"), normalized["salary_min"], normalized["salary_max"]):
            continue
        if not _matches_optional_range(row.get("minutes"), normalized["minutes_min"], None):
            continue
        if not _passes_score_filters(row, normalized):
            continue

        results.append(row)

    return results


def sort_scout_results(rows: list[dict], sort_by: str, descending: bool = True) -> list[dict]:
    """Sort scout result rows by an allowed numeric column."""
    sort_column = ADVANCED_SORT_COLUMNS.get(sort_by, "overall_role_score")
    return sorted(
        rows,
        key=lambda row: (
            parse_float(row.get(sort_column)) if parse_float(row.get(sort_column)) is not None else -1.0,
            parse_float(row.get("minutes")) or 0.0,
        ),
        reverse=descending,
    )


def advanced_search_players(
    filters: dict,
    players: list[dict[str, str]] | None = None,
    view_path: str | Path = DEFAULT_VIEW_PATH,
) -> list[dict[str, object]]:
    """Run the Button 4 advanced search flow and return frontend-ready rows."""
    normalized = validate_advanced_filters(filters)
    filtered_rows = apply_advanced_filters(normalized, players=players, view_path=view_path)
    sorted_rows = sort_scout_results(
        filtered_rows,
        str(normalized["sort_by"]),
        descending=normalized["sort_direction"] != "asc",
    )
    top_n = int(normalized["top_n"])
    return [_build_advanced_result_row(row, str(normalized["sort_by"])) for row in sorted_rows[:top_n]]


def _build_advanced_result_row(row: dict[str, str], sort_by: str) -> dict[str, object]:
    sort_column = ADVANCED_SORT_COLUMNS.get(sort_by, "overall_role_score")
    result: dict[str, object] = {}
    for field in ADVANCED_RESULT_FIELDS:
        if field in {"age", "minutes", "salary_annual_gross_eur", "overall_role_score", "salary_value_score", "salary_efficiency_score"}:
            result[field] = parse_float(row.get(field))
        else:
            result[field] = row.get(field, "")

    result["selected_sort_by"] = sort_by
    result["selected_sort_score"] = parse_float(row.get(sort_column))
    return result


def _passes_score_filters(row: dict[str, str], filters: dict[str, object]) -> bool:
    for filter_key, column in ADVANCED_SCORE_FILTER_COLUMNS.items():
        minimum = filters.get(filter_key)
        if minimum is None:
            continue
        if not _matches_number_range(row.get(column), parse_float(minimum), None):
            return False
    return True


def _matches_optional_range(value: str | None, minimum: object = None, maximum: object = None) -> bool:
    min_value = parse_float(minimum)
    max_value = parse_float(maximum)
    if min_value is None and max_value is None:
        return True
    return _matches_number_range(value, min_value, max_value)


def _range_is_reversed(minimum: object, maximum: object) -> bool:
    min_value = parse_float(minimum)
    max_value = parse_float(maximum)
    return min_value is not None and max_value is not None and min_value > max_value


def _parse_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_bool_option(value: object, default: bool) -> bool:
    parsed = parse_bool(value)
    return default if parsed is None else parsed
