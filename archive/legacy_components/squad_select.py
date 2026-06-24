from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st

from components.cards import player_card_html
from components.player_modal import render_player_detail_modal
from src.data_loader import filter_players
from src.coach.formations import FORMATIONS, ROLE_ALIASES
from src.coach.scoring import role_score


def _first_query_value(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def render_player_list_panel(
    players: pd.DataFrame,
    *,
    lineup_state_key: str = "lineup",
    filter_state_key: str = "filter_group",
    key_prefix: str = "squad",
) -> None:
    """좌측 선수 목록 패널을 렌더링합니다."""
    st.session_state.setdefault(filter_state_key, "전체")
    st.markdown("### 선수 목록")

    keyword = st.text_input(
        "선수 이름 검색",
        placeholder="선수 이름, 구단, 국가 검색",
        label_visibility="collapsed",
        key=f"{key_prefix}_player_keyword",
    )

    group_cols = st.columns(5)
    for idx, group in enumerate(["전체", "GK", "DF", "MF", "FW"]):
        is_active = st.session_state.get(filter_state_key) == group
        label = f"✓ {group}" if is_active else group

        if group_cols[idx].button(label, key=f"{key_prefix}_filter_{group}", use_container_width=True):
            st.session_state[filter_state_key] = group
            st.rerun()

    filtered = filter_players(players, keyword, st.session_state[filter_state_key])
    lineup = st.session_state.get(lineup_state_key, {})
    selected_names = {name for name in lineup.values() if name}

    with st.container(height=620, border=False):
        if filtered.empty:
            st.info("조건에 맞는 선수가 없습니다.")
            return

        for _, row in filtered.iterrows():
            player = row.to_dict()
            selected = player["name"] in selected_names

            st.markdown(player_card_html(player, selected=selected), unsafe_allow_html=True)

            number = int(player.get("number", 0) or 0)
            number_text = f"#{number}" if number else "#-"

            if st.button(
                f" {player['name']} 상세 정보 보기",
                key=f"{key_prefix}_open_modal_{player['name']}",
                use_container_width=True,
            ):
                render_player_detail_modal(player)


def slot_group(role: str) -> str:
    role = str(role).upper()

    if role == "GK":
        return "GK"
    if role in ["CB", "LB", "RB", "LWB", "RWB"]:
        return "DF"
    if role in ["CM", "DM", "CDM", "AM", "CAM", "LM", "RM"]:
        return "MF"
    if role in ["ST", "CF", "LW", "RW", "LF", "RF"]:
        return "FW"

    return "전체"


def get_slot_info(formation: str, slot_id: str) -> dict | None:
    for slot in FORMATIONS.get(formation, []):
        if str(slot["slot_id"]) == str(slot_id):
            return slot
    return None


def get_query_slot() -> str | None:
    return _first_query_value(st.query_params.get("slot"))


def clear_slot_query(page: str | None = None) -> None:
    page_key = page or st.session_state.get("current_page", "coach_squad")
    st.query_params.clear()
    st.query_params["page"] = page_key


def _filter_available_players(
    players: pd.DataFrame,
    *,
    role: str,
    selected_names: set[str],
) -> pd.DataFrame:
    available = players.copy()

    if "name" in available.columns:
        available = available[~available["name"].isin(selected_names)]

    aliases = set(ROLE_ALIASES.get(str(role).upper(), [str(role).upper()]))
    group = slot_group(role)

    if {"position", "detail_position"}.issubset(available.columns):
        position_upper = available["position"].astype(str).str.upper()
        detail_upper = available["detail_position"].astype(str).str.upper()

        matched = position_upper.isin(aliases) | detail_upper.isin(aliases)

        # 상세 포지션이 부족한 데이터도 표시되도록 그룹 기준을 보조로 허용합니다.
        if group != "전체":
            matched = matched | position_upper.eq(group)

        filtered = available[matched].copy()
    elif "position" in available.columns and group != "전체":
        filtered = available[available["position"].astype(str).str.upper().eq(group)].copy()
    else:
        filtered = available.copy()

    # 엄격 필터로 후보가 0명이면 그룹 필터로 한 번 완화합니다.
    if filtered.empty and group != "전체" and "position" in available.columns:
        filtered = available[available["position"].astype(str).str.upper().eq(group)].copy()

    # 그래도 없으면 선수 없음만 표시하는 대신 전체 미선택 선수라도 보여줍니다.
    if filtered.empty:
        filtered = available.copy()

    if not filtered.empty:
        filtered = filtered.copy()
        filtered["_fit_score"] = filtered.apply(lambda row: role_score(row, role), axis=1)
        filtered = filtered.sort_values("_fit_score", ascending=False)

    return filtered.reset_index(drop=True)


def render_slot_player_modal(
    players: pd.DataFrame,
    slot_id: str,
    *,
    formation_state_key: str = "formation",
    lineup_state_key: str = "lineup",
    page: str | None = None,
    sync_query_state: Callable[[], None] | None = None,
    key_prefix: str = "squad",
) -> None:
    """경기장 슬롯 클릭 후, 해당 포지션 조건에 맞는 선수 선택 모달을 띄웁니다."""
    formation = st.session_state.get(formation_state_key)
    lineup = st.session_state.setdefault(lineup_state_key, {})

    if formation not in FORMATIONS:
        if sync_query_state is not None:
            sync_query_state()
        else:
            clear_slot_query(page)
        return

    slot = get_slot_info(formation, slot_id)
    if slot is None:
        if sync_query_state is not None:
            sync_query_state()
        else:
            clear_slot_query(page)
        return

    slot_id = str(slot["slot_id"])
    role = str(slot.get("role", slot_id))

    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dialog is None:
        st.warning("현재 Streamlit 버전에서는 모달 기능을 지원하지 않습니다. streamlit을 업그레이드해 주세요.")
        return

    @dialog(f"{role} 포지션 선수 선택")
    def _slot_dialog() -> None:
        current_player = lineup.get(slot_id, "")

        selected_names = {
            name
            for key, name in lineup.items()
            if str(key) != slot_id and name
        }

        available = _filter_available_players(
            players,
            role=role,
            selected_names=selected_names,
        )

        options = ["선수 없음"] + available["name"].astype(str).tolist()
        default_index = options.index(current_player) if current_player in options else 0

        selected_player = st.selectbox(
            f"{role} 슬롯에 배치할 선수",
            options,
            index=default_index,
            key=f"{key_prefix}_slot_select_{slot_id}",
        )

        if selected_player != "선수 없음" and not available.empty:
            selected_row = available[available["name"].astype(str).eq(selected_player)]
            if not selected_row.empty and "_fit_score" in selected_row.columns:
                st.caption(f"포지션 적합도: {int(round(selected_row.iloc[0]['_fit_score']))}점")

        st.caption("이미 다른 포지션에 배치된 선수는 제외됩니다.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("배치하기", type="primary", use_container_width=True, key=f"{key_prefix}_slot_apply_{slot_id}"):
                lineup[slot_id] = "" if selected_player == "선수 없음" else selected_player
                st.session_state[lineup_state_key] = lineup
                if sync_query_state is not None:
                    sync_query_state()
                else:
                    clear_slot_query(page)
                st.rerun()

        with col2:
            if st.button("비우기", use_container_width=True, key=f"{key_prefix}_slot_clear_{slot_id}"):
                lineup[slot_id] = ""
                st.session_state[lineup_state_key] = lineup
                if sync_query_state is not None:
                    sync_query_state()
                else:
                    clear_slot_query(page)
                st.rerun()

        if st.button("닫기", use_container_width=True, key=f"{key_prefix}_slot_close_{slot_id}"):
            if sync_query_state is not None:
                sync_query_state()
            else:
                clear_slot_query(page)
            st.rerun()

    _slot_dialog()
