from __future__ import annotations

import streamlit as st

from src.constants import DEFAULT_FORMATION
from src.coach.formations import FORMATIONS


def _first_query_value(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def get_empty_lineup(formation: str) -> dict[str, str]:
    if formation not in FORMATIONS:
        formation = DEFAULT_FORMATION

    return {str(slot["slot_id"]): "" for slot in FORMATIONS[formation]}


def init_lineup_state() -> None:
    st.session_state.setdefault("formation", DEFAULT_FORMATION)
    st.session_state.setdefault("lineup", get_empty_lineup(DEFAULT_FORMATION))
    st.session_state.setdefault("filter_group", "전체")
    ensure_lineup_keys()


def ensure_lineup_keys() -> None:
    formation = st.session_state.get("formation", DEFAULT_FORMATION)

    if formation not in FORMATIONS:
        formation = DEFAULT_FORMATION
        st.session_state.formation = formation

    current_lineup = st.session_state.get("lineup", {})
    st.session_state.lineup = {
        str(slot["slot_id"]): current_lineup.get(str(slot["slot_id"]), "")
        for slot in FORMATIONS[formation]
    }


def _set_page_query(page: str = "coach_squad") -> None:
    st.query_params.clear()
    st.query_params["page"] = page


def set_formation(formation: str) -> None:
    if formation not in FORMATIONS:
        return

    old_lineup = st.session_state.get("lineup", {})
    st.session_state.formation = formation
    st.session_state.lineup = {
        str(slot["slot_id"]): old_lineup.get(str(slot["slot_id"]), "")
        for slot in FORMATIONS[formation]
    }
    _set_page_query("coach_squad")


def set_lineup(lineup: dict[str, str]) -> None:
    st.session_state.lineup = lineup
    ensure_lineup_keys()
    _set_page_query("coach_squad")


def reset_lineup() -> None:
    st.session_state.lineup = get_empty_lineup(st.session_state.formation)
    _set_page_query("coach_squad")


def get_requested_slot() -> str | None:
    return _first_query_value(st.query_params.get("slot"))


def clear_slot_query(page: str = "coach_squad") -> None:
    _set_page_query(page)


# 기존 코드 호환용: 이제 라인업은 URL에 저장하지 않습니다.
def encode_lineup(lineup: dict) -> str:
    return ""


def decode_lineup(encoded: str) -> dict:
    return {}


def sync_query_state(page: str | None = None) -> None:
    _set_page_query(page or st.session_state.get("current_page", "coach_squad"))


def restore_state_from_query() -> None:
    return None
