"""Query helpers for scout search buttons."""

from __future__ import annotations

from pathlib import Path

from src.scout.scout_features import DEFAULT_VIEW_PATH, parse_bool, parse_float, read_csv_rows


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

VALUE_FOCUS_SORT_COLUMNS = {
    "undervalued": ("salary_value_score", True),
    "overvalued": ("salary_value_score", False),
    "salary_gap": ("salary_gap_eur", True),
    "balanced": ("salary_efficiency_score", True),
}

METRIC_FOCUS_SCORE_COLUMNS = {
    "overall": ["overall_role_score"],
    "attack": ["attack_score", "shooting_score"],
    "passing": ["chance_creation_score", "creative_pass_score", "progressive_pass_score"],
    "defense": ["defensive_action_score", "ball_winning_score", "aerial_defense_score"],
    "physical": ["pressing_score", "aerial_defense_score"],
    "balanced": ["overall_role_score"],
}

SIMILARITY_FOCUS_OPTIONS = [
    {
        "value": "overall",
        "label": "전체 스타일 유사",
        "description": "역할 적합도, 공격, 찬스 창출, 압박, 수비, 연봉 효율을 함께 비교합니다.",
    },
    {
        "value": "role",
        "label": "역할 적합도 유사",
        "description": "사전에 정의한 역할별 적합도 점수 분포를 비교합니다.",
    },
    {
        "value": "attack",
        "label": "공격 성향 유사",
        "description": "공격, 슈팅, 찬스 창출 점수를 중심으로 비교합니다.",
    },
    {
        "value": "passing",
        "label": "창의성/전개 성향 유사",
        "description": "찬스 창출, 창의 패스, 전진 패스, 빌드업 proxy 점수를 기준으로 비교합니다.",
    },
    {
        "value": "defense",
        "label": "수비 성향 유사",
        "description": "수비 행동, 볼 탈취, 공중볼 수비 점수를 중심으로 비교합니다.",
    },
    {
        "value": "physical",
        "label": "압박/활동량 성향 유사",
        "description": "압박, 공중볼 수비, 출전 시간 percentile을 함께 비교합니다.",
    },
    {
        "value": "value",
        "label": "가성비 대체 후보",
        "description": "기량 점수와 연봉 효율, 연봉 가치 점수를 함께 고려합니다.",
    },
]

POSITION_SCOPE_OPTIONS = [
    {
        "value": "same_position",
        "label": "같은 포지션",
        "description": "기준 선수와 같은 포지션 그룹 안에서만 찾습니다.",
    },
    {
        "value": "adjacent_position",
        "label": "인접 포지션 포함",
        "description": "전술적으로 가까운 포지션 그룹까지 확장해서 찾습니다.",
    },
    {
        "value": "all",
        "label": "전체 포지션",
        "description": "포지션 제한 없이 유사한 점수 분포를 가진 선수를 찾습니다.",
    },
]

SIMILARITY_FEATURE_COLUMNS = {
    "overall": [
        "overall_role_score",
        "attack_score",
        "shooting_score",
        "chance_creation_score",
        "pressing_score",
        "defensive_action_score",
        "salary_efficiency_score",
    ],
    "role": list(ROLE_SCORE_COLUMNS.values()),
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
    "GK": {"GK"},
    "DF": {"DF", "MF"},
    "MF": {"DF", "MF", "FW"},
    "FW": {"MF", "FW"},
}


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


def get_player_search_options(
    keyword: str,
    players: list[dict[str, str]] | None = None,
    view_path: str | Path = DEFAULT_VIEW_PATH,
    limit: int = 20,
) -> list[dict[str, str]]:
    """Return player search options for salary diagnosis and similarity search."""
    rows = players if players is not None else load_scout_player_view(view_path)
    normalized_keyword = str(keyword or "").strip().lower()
    if not normalized_keyword:
        return []

    matches: list[dict[str, str]] = []
    for row in rows:
        player_name = row.get("player_name", "")
        if normalized_keyword not in player_name.lower():
            continue
        matches.append(
            {
                "value": row.get("player_id", ""),
                "label": (
                    f"{player_name} · {row.get('team', '')} · {row.get('league', '')} · "
                    f"{row.get('position_group', '')} · {row.get('age', '')}세"
                ),
                "player_name": player_name,
                "team": row.get("team", ""),
                "league": row.get("league", ""),
                "position_group": row.get("position_group", ""),
                "age": row.get("age", ""),
            }
        )

    matches.sort(key=lambda item: (item["player_name"].lower(), item["team"].lower(), item["league"].lower()))
    return matches[:limit]


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


def evaluate_player_value(
    player_id: str,
    options: dict | None = None,
    players: list[dict[str, str]] | None = None,
    view_path: str | Path = DEFAULT_VIEW_PATH,
) -> dict[str, object] | None:
    """Return Button 2 salary-value diagnosis for one selected player."""
    rows = players if players is not None else load_scout_player_view(view_path)
    option_values = options or {}
    metric_focus = str(option_values.get("metric_focus") or "overall")
    comparison_scope = str(option_values.get("comparison_scope") or "same_position")
    min_minutes = parse_float(option_values.get("min_minutes"))

    for row in rows:
        if row.get("player_id") != player_id:
            continue

        warnings = _build_value_warnings(row, min_minutes)
        return {
            "player_id": row.get("player_id", ""),
            "player_name": row.get("player_name", ""),
            "team": row.get("team", ""),
            "league": row.get("league", ""),
            "position_group": row.get("position_group", ""),
            "age": parse_float(row.get("age")),
            "minutes": parse_float(row.get("minutes")),
            "metric_focus": metric_focus,
            "comparison_scope": comparison_scope,
            "metric_score": _metric_focus_score(row, metric_focus),
            "salary_value_label": row.get("salary_value_label", "평가 불가"),
            "salary_value_status": row.get("salary_value_status", "unknown"),
            "salary_value_score": parse_float(row.get("salary_value_score")),
            "current_salary_annual_gross_eur": parse_float(
                row.get("current_salary_annual_gross_eur") or row.get("salary_annual_gross_eur")
            ),
            "predicted_next_salary_annual_gross_eur": parse_float(row.get("predicted_next_salary_annual_gross_eur")),
            "salary_gap_eur": parse_float(row.get("salary_gap_eur")),
            "salary_gap_pct": parse_float(row.get("salary_gap_pct")),
            "performance_percentile": parse_float(row.get("performance_percentile_by_position")),
            "salary_percentile": parse_float(row.get("salary_percentile_by_position")),
            "minutes_percentile": parse_float(row.get("minutes_percentile_by_position")),
            "salary_efficiency_score": parse_float(row.get("salary_efficiency_score")),
            "prediction_model_version": row.get("prediction_model_version", ""),
            "prediction_confidence": parse_float(row.get("prediction_confidence")),
            "reason_summary": row.get("value_reason_summary", ""),
            "warnings": warnings,
        }

    return None


def find_salary_value_players(
    filters: dict,
    players: list[dict[str, str]] | None = None,
    view_path: str | Path = DEFAULT_VIEW_PATH,
) -> list[dict[str, object]]:
    """Return ranked Button 2 salary-value candidates."""
    rows = players if players is not None else load_scout_player_view(view_path)
    position_group = str(filters.get("position_group") or "ALL").upper()
    league = str(filters.get("league") or "ALL")
    value_focus = str(filters.get("value_focus") or "undervalued")
    top_n = int(filters.get("top_n") or 20)
    age_min = parse_float(filters.get("age_min"))
    age_max = parse_float(filters.get("age_max"))
    min_minutes = parse_float(filters.get("min_minutes"))
    sort_column, descending = VALUE_FOCUS_SORT_COLUMNS.get(value_focus, VALUE_FOCUS_SORT_COLUMNS["undervalued"])

    results: list[dict[str, object]] = []
    for row in rows:
        if row.get("salary_available") != "true" or row.get("score_available") != "true":
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

        result = dict(row)
        result["result_score"] = parse_float(row.get(sort_column)) or 0.0
        result["selected_value_focus"] = value_focus
        results.append(result)

    results.sort(
        key=lambda row: (
            parse_float(row.get(sort_column)) or 0.0,
            parse_float(row.get("overall_role_score")) or 0.0,
        ),
        reverse=descending,
    )
    return results[:top_n]


def build_player_feature_vector(player: dict[str, str], focus: str) -> dict[str, float]:
    """Build the feature vector used by Button 3 similarity search."""
    columns = SIMILARITY_FEATURE_COLUMNS.get(focus, SIMILARITY_FEATURE_COLUMNS["overall"])
    vector: dict[str, float] = {}
    for column in columns:
        value = parse_float(player.get(column))
        vector[column] = 50.0 if value is None else max(0.0, min(value, 100.0))
    return vector


def calculate_similarity_score(
    base_vector: dict[str, float],
    candidate_vector: dict[str, float],
    focus: str,
) -> float:
    """Calculate a 0-100 similarity score with weighted distance."""
    columns = SIMILARITY_FEATURE_COLUMNS.get(focus, SIMILARITY_FEATURE_COLUMNS["overall"])
    if not columns:
        return 0.0

    total_weight = 0.0
    weighted_distance = 0.0
    for column in columns:
        weight = 1.0
        if focus == "role" and column.startswith("role_fit_"):
            weight = 1.15
        elif focus == "value" and column in {"salary_efficiency_score", "salary_value_score"}:
            weight = 1.25
        elif focus == "passing" and column in {"chance_creation_score", "creative_pass_score"}:
            weight = 1.2

        weighted_distance += abs(base_vector.get(column, 50.0) - candidate_vector.get(column, 50.0)) * weight
        total_weight += weight

    average_distance = weighted_distance / total_weight if total_weight else 100.0
    return round(max(0.0, min(100.0, 100.0 - average_distance)), 2)


def find_similar_players(
    filters: dict,
    players: list[dict[str, str]] | None = None,
    view_path: str | Path = DEFAULT_VIEW_PATH,
) -> list[dict[str, object]]:
    """Return ranked Button 3 similar-player candidates."""
    rows = players if players is not None else load_scout_player_view(view_path)
    base_player_id = str(filters.get("base_player_id") or "")
    focus = str(filters.get("similarity_focus") or "overall")
    if focus not in SIMILARITY_FEATURE_COLUMNS:
        focus = "overall"

    position_scope = str(filters.get("position_scope") or "same_position")
    league = str(filters.get("league") or "ALL")
    top_n = int(filters.get("top_n") or 20)
    age_max = parse_float(filters.get("age_max"))
    max_salary = parse_float(filters.get("max_salary"))
    min_minutes = parse_float(filters.get("min_minutes"))
    if min_minutes is None:
        min_minutes = 700.0

    base_player = next((row for row in rows if row.get("player_id") == base_player_id), None)
    if base_player is None or base_player.get("score_available") != "true":
        return []

    base_vector = build_player_feature_vector(base_player, focus)
    allowed_positions = _allowed_position_groups(base_player.get("position_group", ""), position_scope)
    results: list[dict[str, object]] = []

    for row in rows:
        if row.get("player_id") == base_player_id:
            continue
        if row.get("score_available") != "true":
            continue
        if allowed_positions is not None and row.get("position_group") not in allowed_positions:
            continue
        if league != "ALL" and row.get("league") != league:
            continue
        if age_max is not None and not _matches_number_range(row.get("age"), None, age_max):
            continue
        if min_minutes is not None and not _matches_number_range(row.get("minutes"), min_minutes, None):
            continue
        if max_salary is not None:
            if row.get("salary_available") != "true":
                continue
            if not _matches_number_range(row.get("salary_annual_gross_eur"), None, max_salary):
                continue

        candidate_vector = build_player_feature_vector(row, focus)
        similarity_score = calculate_similarity_score(base_vector, candidate_vector, focus)
        result = {
            "player_id": row.get("player_id", ""),
            "player_name": row.get("player_name", ""),
            "team": row.get("team", ""),
            "league": row.get("league", ""),
            "position_group": row.get("position_group", ""),
            "age": parse_float(row.get("age")),
            "minutes": parse_float(row.get("minutes")),
            "salary_annual_gross_eur": parse_float(row.get("salary_annual_gross_eur")),
            "similarity_score": similarity_score,
            "similarity_label": _similarity_label(similarity_score),
            "similarity_focus": focus,
            "base_player_id": base_player.get("player_id", ""),
            "base_player_name": base_player.get("player_name", ""),
            "salary_value_label": row.get("salary_value_label", "평가 불가"),
            "salary_value_score": parse_float(row.get("salary_value_score")),
            "data_quality_note": row.get("data_quality_note", ""),
            "similarity_reason_summary": _build_similarity_reason(base_player, row, focus, similarity_score),
        }
        results.append(result)

    results.sort(
        key=lambda row: (
            parse_float(row.get("similarity_score")) or 0.0,
            parse_float(row.get("minutes")) or 0.0,
        ),
        reverse=True,
    )
    return results[:top_n]


def _metric_focus_score(row: dict[str, str], metric_focus: str) -> float:
    columns = METRIC_FOCUS_SCORE_COLUMNS.get(metric_focus, METRIC_FOCUS_SCORE_COLUMNS["overall"])
    values = [parse_float(row.get(column)) for column in columns]
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return 0.0
    return round(sum(valid_values) / len(valid_values), 2)


def _build_value_warnings(row: dict[str, str], min_minutes: float | None) -> list[str]:
    warnings: list[str] = []
    minutes = parse_float(row.get("minutes"))
    if min_minutes is not None and minutes is not None and minutes < min_minutes:
        warnings.append("below_selected_minutes_threshold")
    if minutes is not None and minutes < 700:
        warnings.append("limited_minutes_sample")
    if row.get("salary_available") != "true":
        warnings.append("salary_unavailable")
    if "passing_proxy_limited" in row.get("data_quality_note", ""):
        warnings.append("passing_proxy_limited")
    if row.get("prediction_model_version") == "baseline_percentile_v1":
        warnings.append("baseline_prediction_until_ml_model")
    return warnings


def _allowed_position_groups(base_position_group: str, position_scope: str) -> set[str] | None:
    base_group = str(base_position_group or "").upper()
    if position_scope == "all":
        return None
    if position_scope == "adjacent_position":
        return ADJACENT_POSITION_GROUPS.get(base_group, {base_group})
    return {base_group}


def _similarity_label(score: float) -> str:
    if score >= 85:
        return "매우 유사"
    if score >= 70:
        return "유사"
    if score >= 55:
        return "부분 유사"
    return "낮은 유사도"


def _build_similarity_reason(base_player: dict[str, str], candidate: dict[str, str], focus: str, score: float) -> str:
    focus_label = next(
        (option["label"] for option in SIMILARITY_FOCUS_OPTIONS if option["value"] == focus),
        "전체 스타일 유사",
    )
    reason = f"{focus_label} 기준으로 {base_player.get('player_name', '기준 선수')}와 {score:.1f}점 유사도를 보입니다."

    base_salary = parse_float(base_player.get("salary_annual_gross_eur"))
    candidate_salary = parse_float(candidate.get("salary_annual_gross_eur"))
    if base_salary and candidate_salary and candidate_salary < base_salary:
        reason += " 기준 선수보다 현재 연봉이 낮아 대체 후보 관점에서도 확인할 가치가 있습니다."

    if focus == "passing" or "passing_proxy_limited" in candidate.get("data_quality_note", ""):
        reason += " 패스/빌드업 관련 점수는 현재 proxy 기반이므로 정밀 패스 데이터 보강 후 재검증이 필요합니다."

    return reason
