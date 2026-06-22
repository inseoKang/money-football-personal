"""Schema helpers for future scout data integration."""

from __future__ import annotations

from collections.abc import Iterable


COLUMN_ALIASES: dict[str, list[str]] = {
    "player_name": ["player_name", "Player", "Name"],
    "age": ["age", "Age"],
    "nation": ["nation", "Nation"],
    "team": ["team", "Squad"],
    "league": ["league", "Comp"],
    "position": ["position", "Pos"],
    "position_group": ["position_group", "Position Group"],
    "minutes": ["minutes", "Min"],
    "nineties": ["nineties", "90s"],
    "salary_eur": ["salary_eur", "Salary", "salary"],
    "predicted_salary_eur": ["predicted_salary_eur", "Predicted Salary"],
    "value_score": ["value_score", "Value Score"],
    "overall_score": ["overall_score", "Overall"],
    "attack_score": ["attack_score", "Attack"],
    "passing_score": ["passing_score", "Passing"],
    "midfield_score": ["midfield_score", "Midfield"],
    "defense_score": ["defense_score", "Defense"],
    "physical_score": ["physical_score", "Physical"],
    "gk_score": ["gk_score", "GK"],
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
