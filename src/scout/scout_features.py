"""Feature engineering for the 25/26 scout player view."""

from __future__ import annotations

import csv
from bisect import bisect_right
from pathlib import Path
from statistics import median
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_PATH = PROJECT_ROOT / "outputs" / "scout_player_base_2526" / "scout_player_base_2526_default.csv"
DEFAULT_VIEW_PATH = PROJECT_ROOT / "data" / "processed" / "scout_player_view_2526.csv"

POSITION_GROUPS = {"FW", "MF", "DF", "GK"}

SAFE_STAT_COLUMNS = [
    "Goals_per90",
    "Shots_per90",
    "SoT_per90",
    "GCA_per90",
    "Tkl_per90",
    "PresAtt3rd_per90",
    "Blocks_per90",
    "BlkSh_per90",
    "BlkPass_per90",
    "Int_per90",
]

SCORE_COLUMNS = [
    "attack_score",
    "shooting_score",
    "chance_creation_score",
    "progressive_pass_score",
    "creative_pass_score",
    "pressing_score",
    "defensive_action_score",
    "ball_winning_score",
    "build_up_score",
    "aerial_defense_score",
    "goalkeeper_score",
]

ROLE_FIT_COLUMNS = [
    "role_fit_finisher",
    "role_fit_pressing_forward",
    "role_fit_creative_midfielder",
    "role_fit_progressive_passer",
    "role_fit_ball_winning_midfielder",
    "role_fit_ball_playing_defender",
    "role_fit_defensive_stopper",
    "role_fit_shot_stopper",
]

SALARY_VALUE_COLUMNS = [
    "current_salary_annual_gross_eur",
    "performance_percentile_by_position",
    "salary_percentile_by_position",
    "salary_percentile_by_league",
    "minutes_percentile_by_position",
    "salary_efficiency_score",
    "predicted_next_salary_annual_gross_eur",
    "predicted_next_salary_log",
    "prediction_model_version",
    "prediction_confidence",
    "salary_gap_eur",
    "salary_gap_pct",
    "salary_value_score",
    "salary_value_status",
    "salary_value_label",
    "value_reason_summary",
]

VIEW_COLUMNS = [
    "player_id",
    "stats_row_id",
    "player_name",
    "nation",
    "team",
    "league",
    "league_country",
    "position",
    "position_group",
    "age",
    "matches_played",
    "starts",
    "minutes",
    "nineties",
    "salary_annual_gross_eur",
    "salary_total_gross_eur",
    "salary_status",
    "salary_active",
    "salary_loan",
    "salary_verified",
    "salary_available",
    "score_available",
    "minutes_bucket",
    "data_quality_note",
    *SCORE_COLUMNS,
    *ROLE_FIT_COLUMNS,
    "overall_role_score",
    *SALARY_VALUE_COLUMNS,
]


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    """Read a CSV as dictionaries using UTF-8 BOM tolerant encoding."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: str | Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    """Write dictionaries to CSV with a stable column order."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_float(value: object) -> float | None:
    """Convert CSV values to float, returning None for blanks or invalid values."""
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_bool(value: object) -> bool | None:
    """Convert common CSV boolean values to bool."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def normalize_position_group(value: object) -> str:
    """Normalize raw positions into FW/MF/DF/GK."""
    text = str(value or "").strip().upper()
    if not text:
        return ""
    first = text.replace("/", ",").replace(";", ",").replace(" ", ",").split(",")[0]
    if first.startswith("GK") or first == "K":
        return "GK"
    if first.startswith("DF") or first == "D":
        return "DF"
    if first.startswith("MF") or first == "M":
        return "MF"
    if first.startswith("FW") or first == "F":
        return "FW"
    return first if first in POSITION_GROUPS else ""


def minutes_bucket(minutes: float | None) -> str:
    """Return a compact playing-time bucket for filters and result badges."""
    if minutes is None:
        return "unknown"
    if minutes >= 2000:
        return "regular"
    if minutes >= 1000:
        return "rotation"
    if minutes >= 300:
        return "limited"
    return "low_sample"


def _percentile_bounds(values: list[float], lower_pct: float = 0.01, upper_pct: float = 0.99) -> tuple[float, float]:
    ordered = sorted(values)
    if not ordered:
        return 0.0, 0.0
    lower_index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * lower_pct)))
    upper_index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * upper_pct)))
    return ordered[lower_index], ordered[upper_index]


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _build_percentile_lookups(rows: list[dict[str, str]], columns: Iterable[str]) -> dict[str, dict[str, list[float]]]:
    lookups: dict[str, dict[str, list[float]]] = {}
    for column in columns:
        lookups[column] = {}
        for group in POSITION_GROUPS:
            values = [
                value
                for row in rows
                if normalize_position_group(row.get("main_position") or row.get("Pos")) == group
                if (value := parse_float(row.get(column))) is not None
            ]
            if not values:
                lookups[column][group] = []
                continue
            lower, upper = _percentile_bounds(values)
            lookups[column][group] = sorted(_clamp(value, lower, upper) for value in values)
    return lookups


def _percentile_score(
    value: float | None,
    column: str,
    position_group: str,
    lookups: dict[str, dict[str, list[float]]],
) -> float | None:
    if value is None:
        return None
    ordered = lookups.get(column, {}).get(position_group, [])
    if not ordered:
        return None
    lower = ordered[0]
    upper = ordered[-1]
    clipped = _clamp(value, lower, upper)
    if lower == upper:
        return 50.0
    return round((bisect_right(ordered, clipped) / len(ordered)) * 100, 2)


def _score_median(scores: Iterable[float | None]) -> float:
    values = [score for score in scores if score is not None]
    if not values:
        return 0.0
    return round(float(median(values)), 2)


def _percentile_from_sorted(value: float | None, ordered: list[float]) -> float | None:
    if value is None or not ordered:
        return None
    lower = ordered[0]
    upper = ordered[-1]
    clipped = _clamp(value, lower, upper)
    return round((bisect_right(ordered, clipped) / len(ordered)) * 100, 2)


def _value_at_percentile(ordered: list[float], percentile: float | None) -> float | None:
    if percentile is None or not ordered:
        return None
    index = int(round((len(ordered) - 1) * (_clamp(percentile, 0.0, 100.0) / 100)))
    return ordered[max(0, min(len(ordered) - 1, index))]


def _weighted_score(parts: list[tuple[float | None, float]]) -> float:
    valid = [(value, weight) for value, weight in parts if value is not None]
    if not valid:
        return 0.0
    total_weight = sum(weight for _, weight in valid)
    if total_weight == 0:
        return 0.0
    return round(sum(value * weight for value, weight in valid) / total_weight, 2)


def _to_output_number(value: float | None, digits: int = 2) -> str:
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return str(round(value, digits))


def _build_quality_note(row: dict[str, str], stat_scores: dict[str, float | None]) -> str:
    notes: list[str] = []
    minutes = parse_float(row.get("Min"))
    salary_available = row.get("salary_match_status") == "matched" and parse_float(row.get("salary_annual_gross_eur")) is not None
    missing_stat_count = sum(1 for value in stat_scores.values() if value is None)

    if minutes is not None and minutes < 300:
        notes.append("low_minutes")
    if not salary_available:
        notes.append("salary_unavailable")
    if missing_stat_count:
        notes.append(f"missing_safe_stats:{missing_stat_count}")
    notes.append("passing_proxy_limited")
    return ";".join(notes)


def build_scout_player_view_rows(base_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Build the processed 25/26 player view with precomputed role-fit scores."""
    lookups = _build_percentile_lookups(base_rows, [*SAFE_STAT_COLUMNS, "Min", "Starts"])
    output_rows: list[dict[str, object]] = []

    for row in base_rows:
        position_group = normalize_position_group(row.get("main_position") or row.get("Pos"))
        minutes = parse_float(row.get("Min"))
        nineties = parse_float(row.get("90s"))
        age = parse_float(row.get("Age"))
        starts = parse_float(row.get("Starts"))
        salary_annual = parse_float(row.get("salary_annual_gross_eur"))
        salary_total = parse_float(row.get("salary_total_gross_eur"))

        stat_scores = {
            column: _percentile_score(parse_float(row.get(column)), column, position_group, lookups)
            for column in SAFE_STAT_COLUMNS
        }
        minutes_score = _percentile_score(minutes, "Min", position_group, lookups)
        starts_score = _percentile_score(starts, "Starts", position_group, lookups)

        shooting_score = _weighted_score(
            [
                (stat_scores["Goals_per90"], 0.55),
                (stat_scores["SoT_per90"], 0.30),
                (stat_scores["Shots_per90"], 0.15),
            ]
        )
        attack_score = _weighted_score(
            [
                (stat_scores["Goals_per90"], 0.40),
                (stat_scores["SoT_per90"], 0.25),
                (stat_scores["Shots_per90"], 0.15),
                (stat_scores["GCA_per90"], 0.20),
            ]
        )
        chance_creation_score = _weighted_score([(stat_scores["GCA_per90"], 0.75), (stat_scores["SoT_per90"], 0.25)])
        progressive_pass_score = _weighted_score(
            [
                (stat_scores["GCA_per90"], 0.45),
                (stat_scores["PresAtt3rd_per90"], 0.30),
                (minutes_score, 0.25),
            ]
        )
        creative_pass_score = _weighted_score([(stat_scores["GCA_per90"], 0.70), (stat_scores["Goals_per90"], 0.30)])
        pressing_score = _weighted_score(
            [
                (stat_scores["PresAtt3rd_per90"], 0.55),
                (stat_scores["Tkl_per90"], 0.25),
                (stat_scores["Blocks_per90"], 0.20),
            ]
        )
        defensive_action_score = _weighted_score(
            [
                (stat_scores["Tkl_per90"], 0.40),
                (stat_scores["Int_per90"], 0.35),
                (stat_scores["Blocks_per90"], 0.25),
            ]
        )
        ball_winning_score = _weighted_score(
            [
                (stat_scores["Tkl_per90"], 0.45),
                (stat_scores["Int_per90"], 0.40),
                (stat_scores["BlkPass_per90"], 0.15),
            ]
        )
        build_up_score = _weighted_score(
            [
                (stat_scores["GCA_per90"], 0.35),
                (stat_scores["PresAtt3rd_per90"], 0.20),
                (minutes_score, 0.25),
                (starts_score, 0.20),
            ]
        )
        aerial_defense_score = _weighted_score(
            [
                (stat_scores["BlkSh_per90"], 0.45),
                (stat_scores["Blocks_per90"], 0.35),
                (stat_scores["Int_per90"], 0.20),
            ]
        )
        goalkeeper_score = _weighted_score([(minutes_score, 0.55), (starts_score, 0.35), (stat_scores["BlkSh_per90"], 0.10)])

        role_fit_finisher = _weighted_score([(shooting_score, 0.70), (attack_score, 0.30)])
        role_fit_pressing_forward = _weighted_score(
            [(pressing_score, 0.50), (attack_score, 0.30), (defensive_action_score, 0.20)]
        )
        role_fit_creative_midfielder = _weighted_score(
            [(chance_creation_score, 0.40), (creative_pass_score, 0.35), (progressive_pass_score, 0.25)]
        )
        role_fit_progressive_passer = _weighted_score([(progressive_pass_score, 0.55), (build_up_score, 0.45)])
        role_fit_ball_winning_midfielder = _weighted_score(
            [(ball_winning_score, 0.45), (defensive_action_score, 0.35), (pressing_score, 0.20)]
        )
        role_fit_ball_playing_defender = _weighted_score(
            [(build_up_score, 0.45), (progressive_pass_score, 0.30), (defensive_action_score, 0.25)]
        )
        role_fit_defensive_stopper = _weighted_score(
            [(defensive_action_score, 0.45), (aerial_defense_score, 0.30), (ball_winning_score, 0.25)]
        )
        role_fit_shot_stopper = goalkeeper_score if position_group == "GK" else 0.0

        score_available = bool(position_group and minutes is not None and minutes > 0 and nineties is not None and nineties > 0)
        salary_available = row.get("salary_match_status") == "matched" and salary_annual is not None

        output_rows.append(
            {
                "player_id": row.get("stats_unique_key") or row.get("player_join_key") or row.get("Player", ""),
                "stats_row_id": row.get("stats_row_id", ""),
                "player_name": row.get("Player", ""),
                "nation": row.get("Nation", ""),
                "team": row.get("Squad", ""),
                "league": row.get("league_canonical", ""),
                "league_country": row.get("league_country", ""),
                "position": row.get("Pos", ""),
                "position_group": position_group,
                "age": _to_output_number(age),
                "matches_played": _to_output_number(parse_float(row.get("MP"))),
                "starts": _to_output_number(starts),
                "minutes": _to_output_number(minutes),
                "nineties": _to_output_number(nineties),
                "salary_annual_gross_eur": _to_output_number(salary_annual),
                "salary_total_gross_eur": _to_output_number(salary_total),
                "salary_status": row.get("salary_status", ""),
                "salary_active": str(parse_bool(row.get("salary_active"))).lower()
                if parse_bool(row.get("salary_active")) is not None
                else "",
                "salary_loan": str(parse_bool(row.get("salary_loan"))).lower()
                if parse_bool(row.get("salary_loan")) is not None
                else "",
                "salary_verified": str(parse_bool(row.get("salary_verified"))).lower()
                if parse_bool(row.get("salary_verified")) is not None
                else "",
                "salary_available": str(salary_available).lower(),
                "score_available": str(score_available).lower(),
                "minutes_bucket": minutes_bucket(minutes),
                "data_quality_note": _build_quality_note(row, stat_scores),
                "attack_score": attack_score,
                "shooting_score": shooting_score,
                "chance_creation_score": chance_creation_score,
                "progressive_pass_score": progressive_pass_score,
                "creative_pass_score": creative_pass_score,
                "pressing_score": pressing_score,
                "defensive_action_score": defensive_action_score,
                "ball_winning_score": ball_winning_score,
                "build_up_score": build_up_score,
                "aerial_defense_score": aerial_defense_score,
                "goalkeeper_score": goalkeeper_score,
                "role_fit_finisher": role_fit_finisher,
                "role_fit_pressing_forward": role_fit_pressing_forward,
                "role_fit_creative_midfielder": role_fit_creative_midfielder,
                "role_fit_progressive_passer": role_fit_progressive_passer,
                "role_fit_ball_winning_midfielder": role_fit_ball_winning_midfielder,
                "role_fit_ball_playing_defender": role_fit_ball_playing_defender,
                "role_fit_defensive_stopper": role_fit_defensive_stopper,
                "role_fit_shot_stopper": role_fit_shot_stopper,
                "overall_role_score": _score_median(
                    [
                        role_fit_finisher,
                        role_fit_pressing_forward,
                        role_fit_creative_midfielder,
                        role_fit_progressive_passer,
                        role_fit_ball_winning_midfielder,
                        role_fit_ball_playing_defender,
                        role_fit_defensive_stopper,
                        role_fit_shot_stopper if position_group == "GK" else None,
                    ]
                ),
            }
        )

    _add_salary_value_columns(output_rows)
    return output_rows


def _add_salary_value_columns(rows: list[dict[str, object]]) -> None:
    """Add Button 2 salary-value diagnosis columns in place.

    The prediction columns intentionally use a baseline percentile model for now.
    A future ML model can overwrite the same columns without changing the frontend contract.
    """
    performance_by_position: dict[str, list[float]] = {}
    salary_by_position: dict[str, list[float]] = {}
    salary_by_league: dict[str, list[float]] = {}
    minutes_by_position: dict[str, list[float]] = {}

    for row in rows:
        position = str(row.get("position_group") or "")
        league = str(row.get("league") or "")
        performance = parse_float(row.get("overall_role_score"))
        salary = parse_float(row.get("salary_annual_gross_eur"))
        minutes = parse_float(row.get("minutes"))

        if position and str(row.get("score_available")) == "true" and performance is not None:
            performance_by_position.setdefault(position, []).append(performance)
        if position and str(row.get("score_available")) == "true" and minutes is not None:
            minutes_by_position.setdefault(position, []).append(minutes)
        if position and str(row.get("salary_available")) == "true" and salary is not None:
            salary_by_position.setdefault(position, []).append(salary)
        if league and str(row.get("salary_available")) == "true" and salary is not None:
            salary_by_league.setdefault(league, []).append(salary)

    for lookup in (performance_by_position, salary_by_position, salary_by_league, minutes_by_position):
        for key in list(lookup):
            lookup[key] = sorted(lookup[key])

    for row in rows:
        position = str(row.get("position_group") or "")
        league = str(row.get("league") or "")
        performance = parse_float(row.get("overall_role_score"))
        salary = parse_float(row.get("salary_annual_gross_eur"))
        minutes = parse_float(row.get("minutes"))

        performance_pct = _percentile_from_sorted(performance, performance_by_position.get(position, []))
        salary_position_pct = _percentile_from_sorted(salary, salary_by_position.get(position, []))
        salary_league_pct = _percentile_from_sorted(salary, salary_by_league.get(league, []))
        minutes_pct = _percentile_from_sorted(minutes, minutes_by_position.get(position, []))

        predicted_salary = _value_at_percentile(salary_by_position.get(position, []), performance_pct)
        salary_efficiency = _build_salary_efficiency_score(performance_pct, salary_position_pct, minutes_pct)
        confidence = _build_prediction_confidence(row, minutes_pct)

        if salary is None or predicted_salary is None or salary <= 0:
            gap_eur = None
            gap_pct = None
            value_score = None
            status = "unknown"
            label = "평가 불가"
        else:
            gap_eur = predicted_salary - salary
            gap_pct = gap_eur / salary
            value_score = _build_salary_value_score(gap_pct, performance_pct, salary_position_pct)
            status, label = _classify_salary_value(gap_pct, performance_pct, salary_position_pct)

        row["current_salary_annual_gross_eur"] = _to_output_number(salary)
        row["performance_percentile_by_position"] = _to_output_number(performance_pct)
        row["salary_percentile_by_position"] = _to_output_number(salary_position_pct)
        row["salary_percentile_by_league"] = _to_output_number(salary_league_pct)
        row["minutes_percentile_by_position"] = _to_output_number(minutes_pct)
        row["salary_efficiency_score"] = _to_output_number(salary_efficiency)
        row["predicted_next_salary_annual_gross_eur"] = _to_output_number(predicted_salary)
        row["predicted_next_salary_log"] = ""
        row["prediction_model_version"] = "baseline_percentile_v1"
        row["prediction_confidence"] = _to_output_number(confidence)
        row["salary_gap_eur"] = _to_output_number(gap_eur)
        row["salary_gap_pct"] = _to_output_number(round(gap_pct * 100, 2) if gap_pct is not None else None)
        row["salary_value_score"] = _to_output_number(value_score)
        row["salary_value_status"] = status
        row["salary_value_label"] = label
        row["value_reason_summary"] = _build_value_reason_summary(
            label,
            performance_pct,
            salary_position_pct,
            gap_pct,
            confidence,
        )


def _build_salary_efficiency_score(
    performance_pct: float | None,
    salary_pct: float | None,
    minutes_pct: float | None,
) -> float | None:
    if performance_pct is None or salary_pct is None:
        return None
    minutes_bonus = ((minutes_pct or 50.0) - 50.0) * 0.10
    return round(_clamp(50.0 + (performance_pct - salary_pct) + minutes_bonus, 0.0, 100.0), 2)


def _build_salary_value_score(
    gap_pct: float,
    performance_pct: float | None,
    salary_pct: float | None,
) -> float:
    percentile_gap = (performance_pct or 0.0) - (salary_pct or 0.0)
    gap_component = _clamp(gap_pct * 50.0, -35.0, 35.0)
    return round(_clamp(50.0 + (percentile_gap * 0.65) + gap_component, 0.0, 100.0), 2)


def _classify_salary_value(
    gap_pct: float,
    performance_pct: float | None,
    salary_pct: float | None,
) -> tuple[str, str]:
    percentile_gap = (performance_pct or 0.0) - (salary_pct or 0.0)
    if gap_pct >= 0.20 and percentile_gap >= 10:
        return "undervalued", "저평가"
    if gap_pct <= -0.20 and percentile_gap <= -10:
        return "overvalued", "고평가"
    return "fair", "적정"


def _build_prediction_confidence(row: dict[str, object], minutes_pct: float | None) -> float:
    confidence = 65.0
    if str(row.get("salary_available")) == "true":
        confidence += 10.0
    if str(row.get("score_available")) == "true":
        confidence += 10.0
    minutes = parse_float(row.get("minutes"))
    if minutes is not None and minutes >= 1000:
        confidence += 10.0
    elif minutes is not None and minutes >= 700:
        confidence += 5.0
    elif minutes is not None and minutes < 300:
        confidence -= 15.0
    if minutes_pct is not None and minutes_pct < 20:
        confidence -= 5.0
    if "passing_proxy_limited" in str(row.get("data_quality_note") or ""):
        confidence -= 5.0
    return round(_clamp(confidence, 0.0, 100.0), 2)


def _build_value_reason_summary(
    label: str,
    performance_pct: float | None,
    salary_pct: float | None,
    gap_pct: float | None,
    confidence: float,
) -> str:
    if performance_pct is None or salary_pct is None or gap_pct is None:
        return "연봉 또는 성능 데이터가 부족해 평가를 확정하기 어렵습니다."

    direction = "높고" if performance_pct >= salary_pct else "낮고"
    gap_text = f"{round(gap_pct * 100, 1)}%"
    return (
        f"같은 포지션 기준 성능 percentile은 {performance_pct:.1f}, "
        f"연봉 percentile은 {salary_pct:.1f}로 성능 위치가 연봉 위치보다 {direction}, "
        f"baseline 예측 연봉과 현재 연봉의 차이는 {gap_text}입니다. "
        f"현재 분류는 {label}이며 예측 신뢰도는 {confidence:.1f}/100입니다."
    )


def build_and_save_scout_player_view(
    base_path: str | Path = DEFAULT_BASE_PATH,
    output_path: str | Path = DEFAULT_VIEW_PATH,
) -> list[dict[str, object]]:
    """Build and save the processed scout player view."""
    rows = build_scout_player_view_rows(read_csv_rows(base_path))
    write_csv_rows(output_path, rows, VIEW_COLUMNS)
    return rows
