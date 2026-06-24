"""Reusable scout candidate recommendation helpers.

현재 데이터셋이 완전하지 않아도 동작하도록 column alias를 사용하고,
추후 백엔드/ML 모델이 붙으면 이 파일의 scoring 부분만 교체할 수 있게 구성합니다.

스카우터 전용 데이터에서는 감독용 role_score()를 사용하지 않고,
scout_player_view_2526.csv에 미리 계산된 role_fit_* 컬럼을 우선 사용합니다.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.scout.scout_query import ROLE_SCORE_COLUMNS
from src.scout.scout_schema import build_column_map


POSITION_GROUPS = {
    "FW": {"FW", "ST", "LW", "RW", "CF", "LF", "RF"},
    "MF": {"MF", "CM", "DM", "CDM", "AM", "CAM", "LM", "RM"},
    "DF": {"DF", "CB", "LB", "RB", "LWB", "RWB"},
    "GK": {"GK"},
}


def _canonical(df: pd.DataFrame, canonical_name: str, column_map: dict[str, str]) -> pd.Series:
    source = column_map.get(canonical_name)
    if source and source in df.columns:
        return df[source]
    return pd.Series([None] * len(df), index=df.index)


def _numeric_series(
    df: pd.DataFrame,
    canonical_name: str,
    column_map: dict[str, str],
    default: float = 0,
) -> pd.Series:
    series = _canonical(df, canonical_name, column_map)
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _number_value(row: pd.Series, column: str | None, default: float = 0) -> float:
    if not column or column not in row.index:
        return default

    value = pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
    if pd.isna(value):
        return default

    return float(value)


def _text_value(row: pd.Series, columns: list[str | None], default: str = "-") -> str:
    for column in columns:
        if not column or column not in row.index:
            continue

        value = str(row.get(column, "")).strip()
        if value and value.lower() != "nan":
            return value

    return default


def _format_money(value: Any) -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").fillna(0).iloc[0]
    number = float(number)

    if number <= 0:
        return "정보 없음"
    if number >= 1_000_000:
        return f"€{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"€{number / 1_000:.0f}K"
    return f"€{number:,.0f}"


def _normalize_0_100(series: pd.Series, *, inverse: bool = False, default: float = 60) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.notna().sum() == 0:
        return pd.Series([default] * len(series), index=series.index)

    numeric = numeric.fillna(numeric.median())
    min_value = float(numeric.min())
    max_value = float(numeric.max())

    if min_value == max_value:
        score = pd.Series([default] * len(series), index=series.index)
    else:
        score = ((numeric - min_value) / (max_value - min_value) * 100).clip(0, 100)

    if inverse:
        score = 100 - score

    return score


def _filter_by_position(
    df: pd.DataFrame,
    conditions: dict[str, Any],
    column_map: dict[str, str],
) -> pd.DataFrame:
    group = str(conditions.get("position_group", "ALL")).upper()

    if group == "ALL":
        return df

    allowed = POSITION_GROUPS.get(group, {group})
    position_column = column_map.get("position", "position")
    group_column = column_map.get("position_group", "position_group")

    if position_column not in df.columns and group_column not in df.columns:
        return df

    mask = pd.Series(False, index=df.index)

    if position_column in df.columns:
        mask = mask | df[position_column].astype(str).str.upper().isin(allowed)

    if group_column in df.columns:
        mask = mask | df[group_column].astype(str).str.upper().isin(allowed)

    filtered = df[mask].copy()
    return filtered if not filtered.empty else df


def _apply_soft_filters(
    df: pd.DataFrame,
    conditions: dict[str, Any],
    column_map: dict[str, str],
) -> pd.DataFrame:
    result = _filter_by_position(df, conditions, column_map)

    age_col = column_map.get("age")
    if age_col in result.columns:
        age_min = int(conditions.get("age_min", 15) or 15)
        age_max = int(conditions.get("age_max", 45) or 45)
        age = pd.to_numeric(result[age_col], errors="coerce")

        # age 정보가 있는 행만 조건 적용.
        # 정보가 없으면 발표용 샘플 데이터가 사라지지 않도록 유지합니다.
        result = result[(age.isna()) | ((age >= age_min) & (age <= age_max))].copy()

    salary_col = column_map.get("salary_eur")
    max_salary = int(conditions.get("max_salary", 0) or 0)

    if salary_col in result.columns and max_salary > 0:
        salary = pd.to_numeric(result[salary_col], errors="coerce").fillna(0)

        # salary가 0이면 정보 없음으로 보고 제외하지 않습니다.
        result = result[(salary <= 0) | (salary <= max_salary)].copy()

    return result


def _score_candidates(
    df: pd.DataFrame,
    conditions: dict[str, Any],
    column_map: dict[str, str],
) -> pd.DataFrame:
    scored = df.copy()

    role_key = str(conditions.get("role_key", "Creative Midfielder"))
    search_type = str(conditions.get("search_type", "role_based"))

    # 스카우터 전용 역할 적합도는 scout_player_view_2526.csv의 role_fit_* 컬럼을 사용합니다.
    role_fit_column = ROLE_SCORE_COLUMNS.get(role_key, "role_fit_creative_midfielder")

    if role_fit_column in scored.columns:
        scored["fit"] = (
            pd.to_numeric(scored[role_fit_column], errors="coerce")
            .fillna(0)
            .round()
            .clip(0, 100)
            .astype(int)
        )
    else:
        scored["fit"] = 0

    # overall_role_score가 있으면 scout_schema alias를 통해 overall_score로 매핑됩니다.
    overall = _numeric_series(scored, "overall_score", column_map, default=0)

    if overall.eq(0).all():
        fallback_score_columns = [
            column_map[canonical]
            for canonical in [
                "attack_score",
                "midfield_score",
                "defense_score",
                "physical_score",
                "gk_score",
            ]
            if canonical in column_map and column_map[canonical] in scored.columns
        ]

        if fallback_score_columns:
            overall = (
                scored[fallback_score_columns]
                .apply(pd.to_numeric, errors="coerce")
                .mean(axis=1)
                .fillna(0)
            )

    scored["overall"] = overall.round().clip(0, 100).astype(int)

    # value_score alias가 salary_value_score를 가리키면, 백엔드가 미리 만든 가치 점수를 우선 사용합니다.
    value_col = column_map.get("value_score")

    if value_col in scored.columns:
        scored["value"] = (
            pd.to_numeric(scored[value_col], errors="coerce")
            .fillna(0)
            .round()
            .clip(0, 100)
            .astype(int)
        )
    else:
        market_value = pd.to_numeric(scored.get("market_value", 0), errors="coerce").fillna(0)
        salary_col = column_map.get("salary_eur")
        salary = (
            pd.to_numeric(scored[salary_col], errors="coerce").fillna(0)
            if salary_col in scored.columns
            else pd.Series([0] * len(scored), index=scored.index)
        )

        market_efficiency = _normalize_0_100(market_value, inverse=True, default=60)
        salary_efficiency = (
            _normalize_0_100(salary, inverse=True, default=60)
            if salary.gt(0).any()
            else market_efficiency
        )

        scored["value"] = (
            scored["overall"] * 0.45
            + scored["fit"] * 0.25
            + market_efficiency * 0.20
            + salary_efficiency * 0.10
        ).round().clip(0, 100).astype(int)

    if search_type == "value":
        scored["final_score"] = (
            scored["value"] * 0.60
            + scored["overall"] * 0.25
            + scored["fit"] * 0.15
        )
    elif search_type == "prospect":
        age_col = column_map.get("age")
        youth_score = (
            _normalize_0_100(scored[age_col], inverse=True, default=70)
            if age_col in scored.columns
            else pd.Series([70] * len(scored), index=scored.index)
        )
        scored["final_score"] = (
            scored["fit"] * 0.35
            + scored["value"] * 0.30
            + youth_score * 0.35
        )
    elif search_type == "similar":
        scored["final_score"] = (
            scored["fit"] * 0.45
            + scored["overall"] * 0.35
            + scored["value"] * 0.20
        )
    else:
        scored["final_score"] = (
            scored["fit"] * 0.50
            + scored["value"] * 0.30
            + scored["overall"] * 0.20
        )

    return scored.sort_values("final_score", ascending=False).reset_index(drop=True)


def _build_strengths(row: pd.Series, column_map: dict[str, str]) -> list[str]:
    candidates = [
        (column_map.get("attack_score", "attack_score"), "공격 기여"),
        (column_map.get("midfield_score", "midfield_score"), "중원 전개"),
        (column_map.get("defense_score", "defense_score"), "수비 안정성"),
        (column_map.get("physical_score", "physical_score"), "압박/피지컬"),
        (column_map.get("gk_score", "gk_score"), "골키핑"),
    ]

    scores: list[tuple[str, float]] = []

    for column, label in candidates:
        if column in row.index:
            scores.append((label, _number_value(row, column, 0)))

    scores = sorted(scores, key=lambda item: item[1], reverse=True)
    return [label for label, score in scores[:2] if score > 0] or ["추가 분석 필요"]


def _build_risk(row: pd.Series, conditions: dict[str, Any]) -> str:
    if int(row.get("fit", 0) or 0) < 75:
        return "역할 적합도가 다른 후보보다 낮아 전술 적응 여부 확인 필요"
    if int(row.get("overall", 0) or 0) < 70:
        return "종합 점수가 낮아 즉시 전력보다는 보완 후보로 검토 필요"
    if conditions.get("search_type") == "prospect":
        return "성장 가능성은 있으나 출전시간과 리그 수준 확인 필요"
    return "계약 조건, 이적 가능성, 리그 적응력 추가 확인 필요"


def recommend_scout_candidates(
    players: pd.DataFrame,
    conditions: dict[str, Any],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Return scout candidates sorted by fit/value score."""
    if players.empty:
        return []

    column_map = build_column_map(players.columns)
    filtered = _apply_soft_filters(players.copy(), conditions, column_map)

    if filtered.empty:
        filtered = players.copy()

    scored = _score_candidates(filtered, conditions, column_map)

    name_col = column_map.get("player_name", "name")
    age_col = column_map.get("age")
    salary_col = column_map.get("salary_eur")
    market_value_col = "market_value" if "market_value" in scored.columns else None

    attack_col = column_map.get("attack_score", "attack_score")
    midfield_col = column_map.get("midfield_score", "midfield_score")
    defense_col = column_map.get("defense_score", "defense_score")
    physical_col = column_map.get("physical_score", "physical_score")
    gk_col = column_map.get("gk_score", "gk_score")

    candidates: list[dict[str, Any]] = []

    for _, row in scored.head(limit).iterrows():
        age_value = row.get(age_col, None) if age_col else None
        age_number = (
            pd.to_numeric(pd.Series([age_value]), errors="coerce").iloc[0]
            if age_value is not None
            else None
        )

        salary_value = row.get(salary_col, 0) if salary_col else 0
        market_value = row.get(market_value_col, 0) if market_value_col else 0

        comment = _text_value(
            row,
            ["comment", "value_reason_summary", "data_quality_note"],
            "데이터 기준으로 스카우팅 후보에 포함되었습니다.",
        )

        candidate = {
            "name": _text_value(row, [name_col, "name"], "Unknown"),
            "club": _text_value(row, [column_map.get("team"), "club"], "-"),
            "nation": _text_value(row, [column_map.get("nation"), "nation"], "-"),
            "age": int(age_number) if pd.notna(age_number) else 0,
            "age_label": f"{int(age_number)}세" if pd.notna(age_number) else "나이 정보 없음",
            "position": _text_value(row, [column_map.get("position"), "position"], "-"),
            "fit": int(row.get("fit", 0) or 0),
            "value": int(row.get("value", 0) or 0),
            "overall": int(row.get("overall", 0) or 0),
            "salary_eur": int(float(salary_value or 0)),
            "salary_label": _format_money(salary_value),
            "market_value": int(float(market_value or 0)),
            "market_value_label": _format_money(market_value),
            "comment": comment,
            "strengths": _build_strengths(row, column_map),
            "risk": _build_risk(row, conditions),
            "attack_score": int(round(_number_value(row, attack_col, 0))),
            "midfield_score": int(round(_number_value(row, midfield_col, 0))),
            "defense_score": int(round(_number_value(row, defense_col, 0))),
            "pace_score": int(round(_number_value(row, "pace_score", 0))),
            "physical_score": int(round(_number_value(row, physical_col, 0))),
            "stamina_score": int(round(_number_value(row, "stamina_score", 0))),
            "gk_score": int(round(_number_value(row, gk_col, 0))),
        }

        candidates.append(candidate)

    return candidates