"""Schema helpers for future scout data integration."""

from __future__ import annotations

from collections.abc import Iterable


COLUMN_ALIASES: dict[str, list[str]] = {
    "player_name": ["player_name", "Player", "Name", "name"],
    "age": ["age", "Age"],
    "nation": ["nation", "Nation"],
    "team": ["team", "Squad", "club"],
    "league": ["league", "Comp"],
    "position": ["position", "Pos"],
    "position_group": ["position_group", "Position Group"],

    "minutes": ["minutes", "Min"],
    "nineties": ["nineties", "90s"],

    "salary_eur": [
        "salary_eur",
        "salary_annual_gross_eur",
        "current_salary_annual_gross_eur",
        "Salary",
        "salary",
    ],
    "predicted_salary_eur": [
        "predicted_salary_eur",
        "predicted_next_salary_annual_gross_eur",
        "Predicted Salary",
    ],

    "value_score": ["value_score", "salary_value_score", "Value Score"],
    "overall_score": ["overall_score", "overall_role_score", "Overall"],

    "attack_score": ["attack_score", "Attack"],
    "passing_score": [
        "passing_score",
        "creative_pass_score",
        "progressive_pass_score",
        "Passing",
    ],
    "midfield_score": [
        "midfield_score",
        "build_up_score",
        "progressive_pass_score",
        "Midfield",
    ],
    "defense_score": ["defense_score", "defensive_action_score", "Defense"],
    "physical_score": ["physical_score", "pressing_score", "aerial_defense_score", "Physical"],
    "gk_score": ["gk_score", "goalkeeper_score", "GK"],
}


def resolve_column_name(
    available_columns: Iterable[str],
    canonical_name: str,
    aliases: dict[str, list[str]] | None = None,
) -> str | None:
    """Return the matching source column name for a canonical scout field."""
    alias_map = aliases or COLUMN_ALIASES
    available_lookup = {column.lower(): column for column in available_columns}

    for candidate in alias_map.get(canonical_name, [canonical_name]):
        match = available_lookup.get(candidate.lower())
        if match:
            return match

    return None


def build_column_map(
    available_columns: Iterable[str],
    aliases: dict[str, list[str]] | None = None,
) -> dict[str, str]:
    """Build a canonical-to-source column map for whatever scout data exists."""
    alias_map = aliases or COLUMN_ALIASES
    return {
        canonical_name: resolved_name
        for canonical_name in alias_map
        if (resolved_name := resolve_column_name(available_columns, canonical_name, alias_map))
    }
