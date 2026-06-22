"""Session state helpers for the scout center flow."""

from __future__ import annotations

from typing import Any

import streamlit as st


SCOUT_MODE_ROLE_BASED = "role_based"
SCOUT_STEP_START = "start"
SCOUT_STEP_FORM = "form"
SCOUT_STEP_RESULT_PENDING = "result_pending"

DEFAULT_ROLE_BASED_CONDITIONS: dict[str, Any] = {
    "position_group": "MF",
    "role_key": "Creative Midfielder",
    "tactical_need": "찬스 메이킹과 전진 패스가 필요함",
    "priority_metrics": ["패스", "중원 전개"],
    "age_min": 18,
    "age_max": 26,
    "max_salary": 3_000_000,
    "min_minutes": 700,
    "league": "ALL",
    "note": "",
}


def init_scout_state() -> None:
    """Initialize scout-related session keys without overwriting user input."""
    st.session_state.setdefault("scout_step", SCOUT_STEP_START)
    st.session_state.setdefault("scout_mode", None)


def open_role_based_form() -> None:
    """Move the scout page into the role-based input step."""
    st.session_state["scout_mode"] = SCOUT_MODE_ROLE_BASED
    st.session_state["scout_step"] = SCOUT_STEP_FORM


def save_role_based_conditions(conditions: dict[str, Any]) -> None:
    """Persist role-based scout inputs for the future result page."""
    st.session_state["scout_mode"] = SCOUT_MODE_ROLE_BASED
    st.session_state["scout_position_group"] = conditions["position_group"]
    st.session_state["scout_role_key"] = conditions["role_key"]
    st.session_state["scout_tactical_need"] = conditions["tactical_need"]
    st.session_state["scout_priority_metrics"] = conditions["priority_metrics"]
    st.session_state["scout_age_min"] = conditions["age_min"]
    st.session_state["scout_age_max"] = conditions["age_max"]
    st.session_state["scout_max_salary"] = conditions["max_salary"]
    st.session_state["scout_min_minutes"] = conditions["min_minutes"]
    st.session_state["scout_league"] = conditions["league"]
    st.session_state["scout_note"] = conditions["note"]
    st.session_state["scout_step"] = SCOUT_STEP_RESULT_PENDING


def get_saved_role_based_conditions() -> dict[str, Any]:
    """Return saved role-based scout inputs with safe fallbacks."""
    defaults = DEFAULT_ROLE_BASED_CONDITIONS
    return {
        "position_group": st.session_state.get("scout_position_group", defaults["position_group"]),
        "role_key": st.session_state.get("scout_role_key", defaults["role_key"]),
        "tactical_need": st.session_state.get("scout_tactical_need", defaults["tactical_need"]),
        "priority_metrics": st.session_state.get(
            "scout_priority_metrics",
            defaults["priority_metrics"],
        ),
        "age_min": st.session_state.get("scout_age_min", defaults["age_min"]),
        "age_max": st.session_state.get("scout_age_max", defaults["age_max"]),
        "max_salary": st.session_state.get("scout_max_salary", defaults["max_salary"]),
        "min_minutes": st.session_state.get("scout_min_minutes", defaults["min_minutes"]),
        "league": st.session_state.get("scout_league", defaults["league"]),
        "note": st.session_state.get("scout_note", defaults["note"]),
    }


def reset_scout_form() -> None:
    """Return to the editable role-based scout form."""
    st.session_state["scout_step"] = SCOUT_STEP_FORM
    st.session_state["scout_mode"] = SCOUT_MODE_ROLE_BASED
