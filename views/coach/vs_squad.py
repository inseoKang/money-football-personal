from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from components.cards import manager_player_card_html, stat_card_html
from components.layout import page_title
from components.metrics_panel import render_metrics_panel
from components.pitch import render_payload_pitch
from src.coach.formation_run import get_available_formations
from src.coach.lineup_payload import evaluate_lineup_payload, get_player_pool_payload, recommend_lineup_payload
from src.coach.player_data import get_laliga_club_options, load_barcelona_players, load_laliga_players
from src.coach.scoring import role_score


DEFAULT_VS_FORMATION = "4-3-3"


METRIC_LABELS = {
    "team_score": "팀 종합 점수",
    "attack": "공격",
    "midfield": "중원",
    "defense": "수비",
    "keeper": "골키퍼",
    "position_fit": "포지션 적합도",
    "balance": "좌우 밸런스",
    "synergy": "선수 시너지",
}


def _first_query_value(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _sync_query_state() -> None:
    st.query_params.clear()
    st.query_params["page"] = "coach_vs_squad"


def _clear_left_player_search() -> None:
    st.session_state["vs_left_player_keyword"] = ""


def _get_query_slot() -> str | None:
    return _first_query_value(st.query_params.get("slot"))


def _available_formations() -> list[str]:
    formations = get_available_formations()
    return formations if formations else [DEFAULT_VS_FORMATION]


def _default_formation() -> str:
    formations = _available_formations()
    return DEFAULT_VS_FORMATION if DEFAULT_VS_FORMATION in formations else formations[0]


def _normalize_lineup(players: pd.DataFrame, lineup: dict) -> dict:
    if players.empty:
        return {}

    valid_ids = set(players["salary_id"].astype(int).tolist())
    name_to_id = {str(row["player"]): int(row["salary_id"]) for _, row in players.iterrows()}
    normalized = {}

    for slot_id, value in dict(lineup or {}).items():
        if value in [None, "", "선수 없음"]:
            normalized[str(slot_id)] = None
            continue

        try:
            salary_id = int(value)
            normalized[str(slot_id)] = salary_id if salary_id in valid_ids else None
            continue
        except (TypeError, ValueError):
            pass

        normalized[str(slot_id)] = name_to_id.get(str(value))

    return normalized


def _init_vs_state(barcelona_players: pd.DataFrame) -> None:
    default = _default_formation()
    formations = _available_formations()

    st.session_state.setdefault("vs_left_formation", default)
    st.session_state.setdefault("vs_right_formation", default)
    st.session_state.setdefault("vs_left_lineup", {})
    st.session_state.setdefault("vs_right_lineup", {})
    st.session_state.setdefault("vs_right_payload_meta", {})
    st.session_state.setdefault("vs_left_filter", "전체")

    if st.session_state.vs_left_formation not in formations:
        st.session_state.vs_left_formation = default

    if st.session_state.vs_right_formation not in formations:
        st.session_state.vs_right_formation = default

    st.session_state.vs_left_lineup = _normalize_lineup(
        barcelona_players,
        st.session_state.vs_left_lineup,
    )


def _render_choice_buttons(
    title: str,
    options: list[str],
    state_key: str,
    key_prefix: str,
    columns_per_row: int | None = None,
) -> tuple[str, bool]:
    st.markdown(
        f"<div class='control-label'>{html.escape(title)}</div>",
        unsafe_allow_html=True,
    )

    if not options:
        return "", False

    if state_key not in st.session_state or st.session_state[state_key] not in options:
        st.session_state[state_key] = options[0]

    changed = False

    # 포메이션 버튼은 한 줄에 고정
    cols = st.columns([1] * len(options), gap="small")

    for col, option in zip(cols, options):
        active = st.session_state[state_key] == option

        if col.button(
            option,
            key=f"{key_prefix}_{option}",
            type="primary" if active else "secondary",
            use_container_width=True,
        ):
            if st.session_state[state_key] != option:
                st.session_state[state_key] = option
                changed = True

    return st.session_state[state_key], changed


def _filter_player_pool(players: list[dict], keyword: str, group: str, selected_ids: set[int]) -> list[dict]:
    keyword = str(keyword or "").strip().lower()
    group = str(group or "전체")
    result = []

    for player in players:
        salary_id = int(player["salaryId"])

        if group != "전체" and player.get("positionGroup") != group:
            continue

        if keyword:
            target = " ".join(
                [
                    str(player.get("name", "")),
                    str(player.get("club", "")),
                    str(player.get("league", "")),
                    str(player.get("country", "")),
                ]
            ).lower()

            if keyword not in target:
                continue

        player = dict(player)
        player["_selected"] = salary_id in selected_ids
        result.append(player)

    return result


def _render_left_player_pool(players: pd.DataFrame) -> None:
    st.markdown("### 바르셀로나 선수 목록")

    search_col, clear_col = st.columns([5, 1])

    with search_col:
        keyword = st.text_input(
            "우리 팀 선수 검색",
            placeholder="선수명, 포지션, 국가 검색",
            label_visibility="collapsed",
            key="vs_left_player_keyword",
        )

    with clear_col:
        st.button(
            "✕",
            key="clear_vs_left_player_search",
            help="검색어 지우기",
            disabled=not bool(keyword),
            on_click=_clear_left_player_search,
            use_container_width=True,
        )

    group_cols = st.columns(5, gap="small")

    for idx, group in enumerate(["전체", "GK", "DF", "MF", "FW"]):
        active = st.session_state.vs_left_filter == group

        if group_cols[idx].button(
            group,
            key=f"vs_left_filter_{group}",
            type="primary" if active else "secondary",
            use_container_width=True,
        ):
            st.session_state.vs_left_filter = group
            st.rerun()

    pool = get_player_pool_payload(players)
    selected_ids = {
        int(value)
        for value in st.session_state.vs_left_lineup.values()
        if value not in [None, ""]
    }
    filtered = _filter_player_pool(pool, keyword, st.session_state.vs_left_filter, selected_ids)

    with st.container(height=580, border=False):
        if not filtered:
            st.info("조건에 맞는 선수가 없습니다.")
            return

        for player in filtered:
            st.markdown(
                manager_player_card_html(player, selected=player.get("_selected", False)),
                unsafe_allow_html=True,
            )


def _get_slot_from_payload(payload: dict, slot_id: str) -> dict | None:
    for slot in payload.get("slots", []):
        if str(slot.get("slotId")) == str(slot_id):
            return slot
    return None


def _candidate_players_for_slot(players: pd.DataFrame, slot: dict, lineup: dict) -> pd.DataFrame:
    role = str(slot.get("role", "CM"))
    accepted = set(slot.get("acceptedPositions", []))
    used_ids = {
        int(value)
        for key, value in lineup.items()
        if str(key) != str(slot.get("slotId")) and value not in [None, ""]
    }

    candidates = players[~players["salary_id"].astype(int).isin(used_ids)].copy()

    if accepted:
        strict = candidates[candidates["position_group"].isin(accepted)].copy()
        if not strict.empty:
            candidates = strict

    if not candidates.empty:
        candidates["_role_fit_score"] = candidates.apply(lambda row: role_score(row, role), axis=1)
        candidates = candidates.sort_values("_role_fit_score", ascending=False)

    return candidates.reset_index(drop=True)


def _render_left_slot_modal(players: pd.DataFrame, payload: dict) -> None:
    requested_slot = _get_query_slot()

    if not requested_slot:
        return

    slot = _get_slot_from_payload(payload, requested_slot)

    if slot is None:
        _sync_query_state()
        st.rerun()
        return

    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

    if dialog is None:
        st.warning("현재 Streamlit 버전에서는 모달 기능을 지원하지 않습니다. streamlit을 업그레이드해 주세요.")
        return

    slot_id = str(slot["slotId"])
    role = str(slot.get("role", slot_id))

    @dialog(f"우리 팀 {role} 선수 선택")
    def _slot_dialog() -> None:
        lineup = st.session_state.setdefault("vs_left_lineup", {})
        current_salary_id = lineup.get(slot_id)
        candidates = _candidate_players_for_slot(players, slot, lineup)

        options = ["선수 없음"]
        option_to_id = {"선수 없음": None}

        for _, row in candidates.iterrows():
            label = (
                f"{row['player']} | {row['club']} | {row['position_group']} "
                f"| 적합도 {round(float(row.get('_role_fit_score', 0)), 1)}"
            )
            options.append(label)
            option_to_id[label] = int(row["salary_id"])

        default_index = 0

        if current_salary_id not in [None, ""]:
            try:
                current_salary_id = int(current_salary_id)

                for index, label in enumerate(options):
                    if option_to_id[label] == current_salary_id:
                        default_index = index
                        break
            except (TypeError, ValueError):
                default_index = 0

        selected_label = st.selectbox(
            f"{role} 슬롯에 배치할 선수",
            options,
            index=default_index,
            key=f"vs_left_slot_select_{slot_id}",
        )
        selected_id = option_to_id[selected_label]

        st.caption("이미 다른 포지션에 배치된 선수는 제외됩니다.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "배치하기",
                type="primary",
                use_container_width=True,
                key=f"vs_left_slot_apply_{slot_id}",
            ):
                lineup[slot_id] = selected_id
                st.session_state.vs_left_lineup = lineup
                _sync_query_state()
                st.rerun()

        with col2:
            if st.button("비우기", use_container_width=True, key=f"vs_left_slot_clear_{slot_id}"):
                lineup[slot_id] = None
                st.session_state.vs_left_lineup = lineup
                _sync_query_state()
                st.rerun()

        if st.button("닫기", use_container_width=True, key=f"vs_left_slot_close_{slot_id}"):
            _sync_query_state()
            st.rerun()

    _slot_dialog()


def _filter_by_club(players: pd.DataFrame, club: str) -> pd.DataFrame:
    return players[players["club"].astype(str).eq(str(club))].copy().reset_index(drop=True)


def _metric_delta(left_metrics: dict, right_metrics: dict) -> dict:
    return {
        key: round(float(left_metrics.get(key, 0)) - float(right_metrics.get(key, 0)), 2)
        for key in METRIC_LABELS
    }


def _winner_text(left_score: float, right_score: float, opponent: str) -> str:
    if abs(left_score - right_score) < 0.5:
        return "무승부에 가까움"

    if left_score > right_score:
        return "Barcelona 우세"

    return f"{opponent} 우세"


def _delta_class(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "neutral"

    if number > 0:
        return "positive"

    if number < 0:
        return "negative"

    return "neutral"


def _delta_row(label: str, value) -> str:
    css_class = _delta_class(value)

    try:
        value_text = f"{float(value):+.2f}"
    except (TypeError, ValueError):
        value_text = str(value)

    return f"""
    <div class="delta-row">
      <div class="delta-label">{html.escape(label)}</div>
      <div class="delta-value {css_class}">{html.escape(value_text)}</div>
    </div>
    """


def _render_delta_panel(delta: dict) -> None:
    st.markdown("#### 전력 차이")
    st.caption("양수는 Barcelona 우세, 음수는 상대 팀 우세입니다.")

    for key, label in METRIC_LABELS.items():
        st.markdown(_delta_row(label, delta.get(key, 0)), unsafe_allow_html=True)


def render() -> None:
    st.session_state.current_page = "coach_vs_squad"
    st.session_state.user_mode = "coach"

    barcelona_players = load_barcelona_players()
    laliga_players = load_laliga_players(exclude_barcelona=True)
    opponent_clubs = get_laliga_club_options(exclude_barcelona=True)

    if barcelona_players.empty:
        st.error("바르셀로나 선수 데이터가 비어 있습니다. data/manager_players.csv의 club 컬럼을 확인해 주세요.")
        return

    if laliga_players.empty or not opponent_clubs:
        st.error("라리가 상대 팀 데이터가 비어 있습니다. manager_players.csv의 league/club 컬럼을 확인해 주세요.")
        return

    _init_vs_state(barcelona_players)

    if "vs_opponent_club" not in st.session_state or st.session_state.vs_opponent_club not in opponent_clubs:
        st.session_state.vs_opponent_club = opponent_clubs[0]

    page_title(
        "VS 스쿼드",
        "Barcelona는 직접 배치하거나 AI 추천을 사용할 수 있고, 상대 라리가 팀은 AI 추천으로만 구성합니다.",
    )

    formations = _available_formations()

    st.markdown("<div class='vs-control-section'>", unsafe_allow_html=True)

    left_control, center_control, right_control = st.columns(
        [1.18, 0.34, 1.18],
        gap="large",
    )

    with left_control:
        st.markdown("<div class='vs-panel-title'>Barcelona 설정</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='vs-panel-desc'>우리 팀 포메이션을 고르고 추천 라인업을 생성합니다.</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='vs-select-spacer'></div>", unsafe_allow_html=True)

        st.markdown("<div class='vs-formation-zone'>", unsafe_allow_html=True)

        left_formation, left_formation_changed = _render_choice_buttons(
            "우리 팀 포메이션",
            formations,
            "vs_left_formation",
            "vs_left_formation_btn",
            columns_per_row=len(formations),
        )

        st.markdown("</div>", unsafe_allow_html=True)

        if left_formation_changed:
            st.session_state.vs_left_lineup = {}
            _sync_query_state()
            st.rerun()

        st.markdown("<div class='vs-ai-button-zone'>", unsafe_allow_html=True)

        if st.button("우리 팀 AI 추천 받기", type="primary", use_container_width=True, key="vs_left_ai_recommend"):
            payload = recommend_lineup_payload(barcelona_players, st.session_state.vs_left_formation)
            st.session_state.vs_left_lineup = payload["lineup"]
            _sync_query_state()
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with center_control:
        st.markdown("<div class='vs-center-box'>", unsafe_allow_html=True)
        st.markdown("<div class='vs-big-text'>VS</div>", unsafe_allow_html=True)

        if st.button("VS 라인업 초기화", use_container_width=True, key="vs_reset_lineup"):
            st.session_state.vs_left_lineup = {}
            st.session_state.vs_right_lineup = {}
            st.session_state.vs_right_payload_meta = {}
            _sync_query_state()
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with right_control:
        st.markdown("<div class='vs-panel-title'>상대 팀 설정</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='vs-panel-desc'>상대 라리가 팀과 포메이션을 선택한 뒤 AI 추천을 생성합니다.</div>",
            unsafe_allow_html=True,
        )

        previous_opponent_club = st.session_state.get("vs_opponent_club", opponent_clubs[0])

        opponent_club = st.selectbox(
            "상대 라리가 팀",
            opponent_clubs,
            index=opponent_clubs.index(previous_opponent_club) if previous_opponent_club in opponent_clubs else 0,
            key="vs_opponent_club_select",
            label_visibility="collapsed",
        )

        if opponent_club != st.session_state.get("vs_opponent_club"):
            st.session_state.vs_opponent_club = opponent_club
            st.session_state.vs_right_lineup = {}
            st.session_state.vs_right_payload_meta = {}
            st.rerun()

        st.markdown("<div class='vs-opponent-formation-zone'>", unsafe_allow_html=True)

        right_formation, right_formation_changed = _render_choice_buttons(
            "상대 팀 포메이션",
            formations,
            "vs_right_formation",
            "vs_right_formation_btn",
            columns_per_row=len(formations),
        )

        st.markdown("</div>", unsafe_allow_html=True)

        if right_formation_changed:
            st.session_state.vs_right_lineup = {}
            st.session_state.vs_right_payload_meta = {}
            st.rerun()

        st.markdown("<div class='vs-ai-button-zone'>", unsafe_allow_html=True)

        if st.button("상대 팀 AI 추천 받기", type="primary", use_container_width=True, key="vs_right_ai_recommend"):
            opponent_players_for_recommend = _filter_by_club(laliga_players, opponent_club)

            payload = recommend_lineup_payload(
                opponent_players_for_recommend,
                st.session_state.vs_right_formation,
            )

            st.session_state.vs_right_lineup = payload["lineup"]
            st.session_state.vs_right_payload_meta = {
                "club": opponent_club,
                "formation": st.session_state.vs_right_formation,
            }

            st.success(f"{opponent_club} AI 추천 라인업을 생성했습니다.")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    opponent_players = _filter_by_club(laliga_players, opponent_club)

    right_meta = st.session_state.get("vs_right_payload_meta", {})

    if right_meta.get("club") != opponent_club or right_meta.get("formation") != st.session_state.vs_right_formation:
        right_lineup = {}
    else:
        right_lineup = st.session_state.vs_right_lineup

    left_payload = evaluate_lineup_payload(
        barcelona_players,
        st.session_state.vs_left_formation,
        st.session_state.vs_left_lineup,
    )

    right_payload = evaluate_lineup_payload(
        opponent_players,
        st.session_state.vs_right_formation,
        right_lineup,
    )

    winner = _winner_text(
        left_payload["metrics"].get("team_score", 0),
        right_payload["metrics"].get("team_score", 0),
        opponent_club,
    )

    delta = _metric_delta(left_payload["metrics"], right_payload["metrics"])

    c1, c2, c3 = st.columns(3)

    c1.markdown(
        stat_card_html("비교 결과", winner, "팀 종합 점수 기준"),
        unsafe_allow_html=True,
    )

    c2.markdown(
        stat_card_html(
            "Barcelona 점수",
            left_payload["metrics"].get("team_score", 0),
            st.session_state.vs_left_formation,
        ),
        unsafe_allow_html=True,
    )

    c3.markdown(
        stat_card_html(
            f"{opponent_club} 점수",
            right_payload["metrics"].get("team_score", 0),
            st.session_state.vs_right_formation,
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    left_list, left_pitch, right_pitch, delta_col = st.columns(
        [1.0, 1.55, 1.55, 1.1],
        gap="medium",
    )

    with left_list:
        _render_left_player_pool(barcelona_players)

    with left_pitch:
        st.markdown("### Barcelona 라인업")

        render_payload_pitch(
            left_payload["slots"],
            page="coach_vs_squad",
            interactive=True,
            caption="Barcelona 슬롯은 직접 선택할 수 있습니다.",
        )

        _render_left_slot_modal(barcelona_players, left_payload)

    with right_pitch:
        st.markdown(f"### {opponent_club} AI 라인업")

        render_payload_pitch(
            right_payload["slots"],
            page="coach_vs_squad_opponent",
            interactive=False,
            caption="상대 팀은 직접 배치할 수 없고 AI 추천만 사용할 수 있습니다.",
        )

    with delta_col:
        _render_delta_panel(delta)

    st.divider()

    left_metrics, right_metrics = st.columns(2, gap="large")

    with left_metrics:
        st.markdown("### Barcelona 지표")

        render_metrics_panel(
            left_payload["metrics"],
            left_payload["formation"],
            ai_comment=left_payload.get("aiComment", ""),
            warnings=left_payload.get("warnings", []),
            title="Barcelona 코멘트",
            comment_source=left_payload.get("commentSource"),
            comment_error=left_payload.get("commentError"),
            prompt_preview=left_payload.get("promptPreview"),
        )

    with right_metrics:
        st.markdown(f"### {opponent_club} 지표")

        render_metrics_panel(
            right_payload["metrics"],
            right_payload["formation"],
            ai_comment=right_payload.get("aiComment", ""),
            warnings=right_payload.get("warnings", []),
            title="상대 팀 코멘트",
            comment_source=right_payload.get("commentSource"),
            comment_error=right_payload.get("commentError"),
            prompt_preview=right_payload.get("promptPreview"),
        )
