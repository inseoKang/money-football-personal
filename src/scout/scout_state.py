"""Session state helpers for the scout center flow."""

from __future__ import annotations

from typing import Any

import streamlit as st


SCOUT_MODE_ROLE_BASED = "role_based"
SCOUT_MODE_VALUE = "value"
SCOUT_MODE_SIMILAR = "similar"
SCOUT_MODE_ADVANCED = "advanced"

SCOUT_STEP_START = "start"
SCOUT_STEP_FORM = "form"
SCOUT_STEP_RESULT_PENDING = "result_pending"

DEFAULT_ROLE_BASED_CONDITIONS: dict[str, Any] = {
    "position_group": "ALL",
    "role_key": "Creative Midfielder",
    "tactical_need": "",
    "priority_metrics": [],
    "age_min": None,
    "age_max": None,
    "max_salary": None,
    "min_minutes": None,
    "league": "ALL",
    "include_loan": True,
    "only_active_salary": False,
    "top_n": 20,
    "note": "",
}

DEFAULT_SCOUT_CONDITIONS: dict[str, Any] = {
    "search_type": SCOUT_MODE_ROLE_BASED,
    "intent_label": "내가 원하는 선수 찾기",
    "request": "역할과 전술 조건에 맞는 선수를 찾고 싶습니다.",
    **DEFAULT_ROLE_BASED_CONDITIONS,
}


# ---- public state helpers -------------------------------------------------


def init_scout_state() -> None:
    """Initialize scout-related session keys without overwriting user input."""
    st.session_state.setdefault("scout_step", SCOUT_STEP_START)
    st.session_state.setdefault("scout_mode", None)
    st.session_state.setdefault("scout_conditions", DEFAULT_SCOUT_CONDITIONS.copy())
    st.session_state.setdefault("selected_scout_candidate_index", 0)


def open_role_based_form() -> None:
    """Move the scout page into the role-based input step."""
    st.session_state["scout_mode"] = SCOUT_MODE_ROLE_BASED
    st.session_state["scout_step"] = SCOUT_STEP_FORM


def save_role_based_conditions(conditions: dict[str, Any]) -> None:
    """Persist role-based scout inputs for the future result page."""
    save_scout_conditions(
        {
            "search_type": SCOUT_MODE_ROLE_BASED,
            "intent_label": "내가 원하는 선수 찾기",
            **conditions,
        }
    )


def get_saved_role_based_conditions() -> dict[str, Any]:
    """Return saved role-based scout inputs with safe fallbacks."""
    conditions = get_scout_conditions()
    return {
        key: conditions.get(key, DEFAULT_ROLE_BASED_CONDITIONS.get(key))
        for key in DEFAULT_ROLE_BASED_CONDITIONS
    }


def reset_scout_form() -> None:
    """Return to the editable role-based scout form."""
    st.session_state["scout_step"] = SCOUT_STEP_FORM
    st.session_state["scout_mode"] = SCOUT_MODE_ROLE_BASED


def save_scout_conditions(conditions: dict[str, Any]) -> None:
    """Persist current scout search conditions for search/result pages."""
    normalized = _normalize_conditions(conditions)
    st.session_state["scout_conditions"] = normalized
    st.session_state["scout_mode"] = normalized["search_type"]
    st.session_state["scout_step"] = SCOUT_STEP_RESULT_PENDING
    st.session_state["selected_scout_candidate_index"] = 0


def get_scout_conditions() -> dict[str, Any]:
    """Return the current scout conditions with safe defaults."""
    conditions = st.session_state.get("scout_conditions")
    if isinstance(conditions, dict):
        return _normalize_conditions(conditions)
    return DEFAULT_SCOUT_CONDITIONS.copy()


def reset_scout_search() -> None:
    """Reset scout flow to the start page."""
    st.session_state["scout_step"] = SCOUT_STEP_START
    st.session_state["scout_mode"] = None
    st.session_state["scout_conditions"] = DEFAULT_SCOUT_CONDITIONS.copy()
    st.session_state["selected_scout_candidate_index"] = 0


# ---- normalizers ----------------------------------------------------------


def _normalize_conditions(conditions: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = DEFAULT_SCOUT_CONDITIONS.copy()
    if conditions:
        merged.update(conditions)

    search_type = str(merged.get("search_type") or SCOUT_MODE_ROLE_BASED)
    if search_type not in {
        SCOUT_MODE_ROLE_BASED,
        SCOUT_MODE_VALUE,
        SCOUT_MODE_SIMILAR,
        SCOUT_MODE_ADVANCED,
    }:
        search_type = SCOUT_MODE_ROLE_BASED

    merged["search_type"] = search_type
    merged["intent_label"] = str(merged.get("intent_label") or _intent_label(search_type))
    merged["request"] = str(merged.get("request") or merged.get("note") or DEFAULT_SCOUT_CONDITIONS["request"])
    merged["position_group"] = str(merged.get("position_group") or "ALL")
    merged["role_key"] = str(merged.get("role_key") or "Creative Midfielder")
    merged["tactical_need"] = str(merged.get("tactical_need") or "")
    merged["league"] = str(merged.get("league") or "ALL")
    merged["team"] = str(merged.get("team") or "ALL")
    merged["note"] = str(merged.get("note") or "")

    merged["age_min"] = _optional_int(merged.get("age_min"))
    merged["age_max"] = _optional_int(merged.get("age_max"))
    merged["max_salary"] = _optional_int(merged.get("max_salary"))
    merged["min_minutes"] = _optional_int(merged.get("min_minutes"))
    merged["top_n"] = _bounded_int(merged.get("top_n"), default=20 if search_type != SCOUT_MODE_ADVANCED else 50, minimum=1, maximum=100)
    merged["include_loan"] = _bool_value(merged.get("include_loan"), True)
    merged["only_active_salary"] = _bool_value(merged.get("only_active_salary"), False)

    priority_metrics = merged.get("priority_metrics")
    if isinstance(priority_metrics, list):
        merged["priority_metrics"] = priority_metrics
    elif priority_metrics:
        merged["priority_metrics"] = [str(priority_metrics)]
    else:
        merged["priority_metrics"] = []

    # Button 2
    merged["player_id"] = str(merged.get("player_id") or "")
    merged["metric_focus"] = str(merged.get("metric_focus") or "overall")
    merged["comparison_scope"] = str(merged.get("comparison_scope") or "same_position")

    # Button 3
    merged["base_player_id"] = str(merged.get("base_player_id") or "")
    merged["similarity_focus"] = str(merged.get("similarity_focus") or "overall")
    merged["position_scope"] = str(merged.get("position_scope") or "same_position")

    # Button 4
    merged["salary_min"] = _optional_int(merged.get("salary_min"))
    merged["salary_max"] = _optional_int(merged.get("salary_max"))
    merged["minutes_min"] = _optional_int(merged.get("minutes_min"), default=700)
    merged["salary_available_only"] = _bool_value(merged.get("salary_available_only"), False)
    merged["score_available_only"] = _bool_value(merged.get("score_available_only"), True)
    merged["salary_value_status"] = str(merged.get("salary_value_status") or "ALL")
    merged["sort_by"] = str(merged.get("sort_by") or "overall_role_score")
    merged["sort_direction"] = str(merged.get("sort_direction") or "desc")

    return merged


def _intent_label(search_type: str) -> str:
    return {
        SCOUT_MODE_ROLE_BASED: "내가 원하는 선수 찾기",
        SCOUT_MODE_VALUE: "25/26 시즌 스탯 기반 선수 측정",
        SCOUT_MODE_SIMILAR: "유사 선수 탐색",
        SCOUT_MODE_ADVANCED: "세밀 조건 검색",
    }.get(search_type, "내가 원하는 선수 찾기")


def _optional_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, "", "None"):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    number = _optional_int(value, default)
    if number is None:
        number = default
    return max(minimum, min(maximum, number))


def _bool_value(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    return default
