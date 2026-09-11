from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from components.cards import manager_player_card_html
from components.layout import page_title
from components.metrics_panel import render_metrics_panel
from components.pitch import render_payload_pitch
from components.player_detail_modal import show_player_detail_dialog
from src.coach.formation_run import get_available_formations, get_formation_slots
from src.coach.formations import ROLE_ALIASES
from src.coach.lineup_payload import evaluate_lineup_payload, recommend_lineup_payload
from src.coach.player_data import load_barcelona_players
from src.coach.scoring import role_score


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _player_payload(player: pd.Series | dict) -> dict:
    return {
        "salaryId": _safe_int(player.get("salary_id", 0)),
        "name": str(player.get("player", "-")),
        "club": str(player.get("club", "-")),
        "league": str(player.get("league", "-")),
        "positionGroup": str(player.get("position_group", "-")),
        "age": _safe_int(player.get("age", 0)),
        "country": str(player.get("country", "-")),
        "scores": {
            "overall": round(
                _safe_float(player.get("overall_score", player.get("overall", 0))),
                2,
            ),
            "attack": round(_safe_float(player.get("attack_score", 0)), 2),
            "defense": round(_safe_float(player.get("defense_score", 0)), 2),
            "keeper": round(_safe_float(player.get("keeper_score", 0)), 2),
            "stamina": round(_safe_float(player.get("stamina_score", 0)), 2),
            "discipline": round(_safe_float(player.get("discipline_score", 0)), 2),
        },
        "stats": {
            "matches": _safe_int(player.get("matches", 0)),
            "minutes": _safe_int(player.get("minutes", 0)),
            "goals": _safe_int(player.get("goals", 0)),
            "assists": _safe_int(player.get("assists", 0)),
        },
    }


def _get_slot(slot_id: str, formation: str) -> dict | None:
    for slot in get_formation_slots(formation):
        if str(slot["slot_id"]) == str(slot_id):
            return slot

    return None


def _accepted_positions(role: str) -> list[str]:
    return ROLE_ALIASES.get(role, [role])


def _used_salary_ids(lineup: dict) -> set[int]:
    used = set()

    for value in lineup.values():
        if value in [None, ""]:
            continue

        try:
            used.add(int(value))
        except (TypeError, ValueError):
            pass

    return used


def _set_detail_player(player_payload: dict) -> None:
    st.session_state["coach_detail_player"] = player_payload


def _clear_player_search() -> None:
    st.session_state["coach_player_search"] = ""


def _clear_slot_query() -> None:
    st.query_params.clear()
    st.query_params["page"] = "coach_squad"


def _init_squad_state(default_formation: str) -> None:
    if "coach_squad_formation" not in st.session_state:
        st.session_state["coach_squad_formation"] = default_formation

    if "coach_squad_lineup" not in st.session_state:
        lineup_from_url = st.query_params.get("lineup")

        if lineup_from_url:
            try:
                restored_lineup = json.loads(lineup_from_url)
                st.session_state["coach_squad_lineup"] = {
                    str(slot_id): int(salary_id)
                    for slot_id, salary_id in restored_lineup.items()
                    if salary_id not in [None, ""]
                }
            except (TypeError, ValueError, json.JSONDecodeError):
                st.session_state["coach_squad_lineup"] = {}
        else:
            st.session_state["coach_squad_lineup"] = {}

    if "coach_position_filter" not in st.session_state:
        st.session_state["coach_position_filter"] = "전체"


def _change_formation(formation: str) -> None:
    current = st.session_state.get("coach_squad_formation")

    if current == formation:
        return

    st.session_state["coach_squad_formation"] = formation
    st.session_state["coach_squad_lineup"] = {}

    _clear_slot_query()
    st.rerun()


def _render_button_filter(
    *,
    label: str,
    options: list[str],
    selected: str,
    key_prefix: str,
) -> str:
    st.markdown(
        f"<div class='squad-control-label'>{label}</div>",
        unsafe_allow_html=True,
    )

    columns = st.columns(len(options))
    next_selected = selected

    for index, option in enumerate(options):
        is_selected = option == selected

        with columns[index]:
            if st.button(
                option,
                key=f"{key_prefix}_{option}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                next_selected = option

    return next_selected


def _render_formation_controls(formations: list[str]) -> str:
    current_formation = st.session_state["coach_squad_formation"]

    with st.container(key="squad_formation_controls"):
        st.markdown(
            "<div class='squad-control-label'>포메이션 선택</div>",
            unsafe_allow_html=True,
        )

        columns = st.columns(len(formations))

        for index, formation in enumerate(formations):
            selected = formation == current_formation

            with columns[index]:
                if st.button(
                    formation,
                    key=f"formation_btn_{formation}",
                    type="primary" if selected else "secondary",
                    use_container_width=True,
                ):
                    _change_formation(formation)

    return st.session_state["coach_squad_formation"]


def _render_player_pool(
    players: pd.DataFrame,
    lineup: dict,
) -> None:
    st.markdown(
        "<div class='squad-player-list-spacer'></div>",
        unsafe_allow_html=True,
    )
    st.markdown("#### 선수 목록")

    used_ids = _used_salary_ids(lineup)

    search_col, clear_col = st.columns([5, 1])

    with search_col:
        search = st.text_input(
            "선수 이름 검색",
            placeholder="선수 이름의 일부를 입력하세요",
            help="입력 후 Enter를 누르거나 입력창 밖을 클릭하면 적용됩니다.",
            key="coach_player_search",
        )

    with clear_col:
        st.markdown(
            "<div class='squad-clear-button-spacer'></div>",
            unsafe_allow_html=True,
        )
        st.button(
            "✕",
            key="clear_coach_player_search",
            help="검색어 지우기",
            disabled=not bool(search),
            on_click=_clear_player_search,
            use_container_width=True,
        )

    selected_position = st.session_state.get("coach_position_filter", "전체")

    next_position = _render_button_filter(
        label="포지션",
        options=["전체", "GK", "DF", "MF", "FW"],
        selected=selected_position,
        key_prefix="position_filter",
    )

    if next_position != selected_position:
        st.session_state["coach_position_filter"] = next_position
        st.rerun()

    position_filter = st.session_state["coach_position_filter"]

    filtered = players.copy()

    if position_filter != "전체":
        filtered = filtered[filtered["position_group"] == position_filter]

    keyword = search.strip().casefold()

    if keyword:
        names = filtered["player"].fillna("").astype(str).str.casefold()
        filtered = filtered[
            names.str.contains(keyword, regex=False, na=False)
        ]

    filtered = filtered.sort_values("overall_score", ascending=False)

    st.caption(f"{len(filtered)}명")

    with st.container(height=560, border=True, key="coach_player_pool"):
        for _, row in filtered.iterrows():
            payload = _player_payload(row)
            salary_id = int(payload["salaryId"])
            selected = salary_id in used_ids

            card_col, button_col = st.columns([4.2, 1])

            with card_col:
                st.markdown(
                    manager_player_card_html(payload, selected=selected),
                    unsafe_allow_html=True,
                )

            with button_col:
                st.markdown("<div class='squad-detail-button-spacer'></div>", unsafe_allow_html=True)

                if st.button(
                    "상세",
                    key=f"detail_pool_{salary_id}",
                    use_container_width=True,
                ):
                    _set_detail_player(payload)
                    st.rerun()

            st.markdown(
                "<div class='squad-player-row-spacer'></div>",
                unsafe_allow_html=True,
            )


@st.dialog("슬롯 선수 선택", width="large")
def _slot_player_dialog(
    players: pd.DataFrame,
    formation: str,
    slot_id: str,
) -> None:
    lineup = st.session_state.get("coach_squad_lineup", {})
    slot = _get_slot(slot_id, formation)

    if slot is None:
        st.error("존재하지 않는 슬롯입니다.")

        if st.button("닫기", use_container_width=True):
            _clear_slot_query()
            st.rerun()

        return

    role = slot["role"]
    accepted_positions = _accepted_positions(role)
    used_ids = _used_salary_ids(lineup)

    st.markdown(f"### {slot_id} · {role}")
    st.caption(f"추천 포지션: {', '.join(accepted_positions)}")

    candidates = players[
        players["position_group"].isin(accepted_positions)
        & (~players["salary_id"].astype(int).isin(used_ids))
    ].copy()

    if candidates.empty:
        st.warning("이 슬롯에 배치할 수 있는 후보가 없습니다.")
    else:
        candidates["roleFitScore"] = candidates.apply(
            lambda player: role_score(player, role),
            axis=1,
        )

        candidates = candidates.sort_values("roleFitScore", ascending=False)

        for _, row in candidates.head(12).iterrows():
            payload = _player_payload(row)
            salary_id = int(payload["salaryId"])
            fit_score = _safe_float(row.get("roleFitScore", 0))

            st.markdown(
                manager_player_card_html(payload, selected=False),
                unsafe_allow_html=True,
            )

            st.caption(f"이 슬롯 적합도: {fit_score:.1f}")

            if st.button(
                "이 슬롯에 배치",
                key=f"assign_{slot_id}_{salary_id}",
                use_container_width=True,
            ):
                lineup[slot_id] = salary_id
                st.session_state["coach_squad_lineup"] = lineup

                _clear_slot_query()
                st.rerun()

            st.divider()

    if st.button("닫기", use_container_width=True):
        _clear_slot_query()
        st.rerun()


def render() -> None:
    st.markdown('<span class="coach-squad-page-marker" aria-hidden="true"></span>', unsafe_allow_html=True)
    st.session_state["current_page"] = "coach_squad"

    page_title(
        "내 스쿼드",
        "Barcelona 선수 데이터를 기반으로 포메이션별 최적 라인업을 구성합니다.",
    )

    players = load_barcelona_players(force_export=False)

    if players.empty:
        st.error("Barcelona 선수 데이터가 비어 있습니다. manager_players.csv와 club 컬럼을 확인해 주세요.")
        return

    formations = get_available_formations()

    default_formation = "4-3-3" if "4-3-3" in formations else formations[0]
    _init_squad_state(default_formation)

    control_col, spacer_col, action_col = st.columns([1.75, 0.18, 1.0])

    with control_col:
        formation = _render_formation_controls(formations)

    with spacer_col:
        st.markdown("<div class='squad-column-spacer'></div>", unsafe_allow_html=True)

    with action_col:
        with st.container(key="squad_action_controls"):
            st.markdown(
                "<div class='squad-control-label'>라인업 액션</div>",
                unsafe_allow_html=True,
            )

            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.button("AI 추천 라인업", use_container_width=True):
                    result = recommend_lineup_payload(players, formation)
                    st.session_state["coach_squad_lineup"] = result["lineup"]
                    st.rerun()

            with btn_col2:
                if st.button("라인업 초기화", use_container_width=True):
                    st.session_state["coach_squad_lineup"] = {}
                    _clear_slot_query()
                    st.rerun()

    st.markdown("<div class='squad-control-spacer'></div>", unsafe_allow_html=True)

    lineup = st.session_state["coach_squad_lineup"]

    result = evaluate_lineup_payload(
        players,
        formation,
        lineup,
    )

    pool_col, pitch_col, metrics_col = st.columns([0.95, 1.65, 1.0])

    with pool_col:
        _render_player_pool(
            players,
            lineup,
        )

    with pitch_col:
        st.markdown(
            "<div class='squad-pitch-spacer'></div>",
            unsafe_allow_html=True,
        )

        render_payload_pitch(
            result["slots"],
            page="coach_squad",
            interactive=True,
            caption="슬롯을 클릭하면 해당 포지션 후보를 선택할 수 있습니다.",
        )

    with metrics_col:
        render_metrics_panel(
            result["metrics"],
            formation,
            ai_comment=result.get("aiComment", ""),
            warnings=result.get("warnings", []),
            title="⚽ AI 감독 코멘트",
            comment_source=result.get("commentSource"),
            comment_error=result.get("commentError"),
            prompt_preview=result.get("promptPreview"),
        )

    slot_id = st.query_params.get("slot")

    if slot_id:
        _slot_player_dialog(
            players,
            formation,
            str(slot_id),
        )

    detail_player = st.session_state.get("coach_detail_player")

    if detail_player:
        show_player_detail_dialog(detail_player)
        st.session_state["coach_detail_player"] = None
