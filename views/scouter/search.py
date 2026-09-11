from __future__ import annotations

import html
from urllib.parse import quote

import streamlit as st

from components.layout import page_title
from components.navigation import move_page
from src.data_loader import load_scout_players
from src.runtime import is_development_mode
from src.scout.scout_query import (
    get_advanced_filter_schema,
    get_player_search_options,
    get_position_scope_options,
    get_role_options,
    get_similarity_focus_options,
    get_tactical_need_options,
)
from src.scout.scout_state import init_scout_state, save_scout_conditions


INTENTS = {
    "role_based": {
        "title": "내가 원하는 선수 찾기",
        "badge": "역할 · 전술 조건",
        "desc": "포지션, 역할, 전술 요구사항을 기준으로 후보를 찾습니다.",
        "request": "역할과 전술 조건에 맞는 선수를 찾고 싶습니다.",
    },
    "value": {
        "title": "연봉 가치 진단",
        "badge": "스탯 기반 선수 측정",
        "desc": "선수 1명을 선택해 저평가/적정/고평가 여부를 확인합니다.",
        "request": "선수의 현재 연봉이 25/26 시즌 스탯 대비 적절한지 평가하고 싶습니다.",
    },
    "similar": {
        "title": "대체 후보 찾기",
        "badge": "유사 선수 탐색",
        "desc": "기준 선수와 스타일이 비슷한 후보를 조건별로 찾습니다.",
        "request": "기준 선수와 비슷한 능력치와 스타일을 가진 대체 후보를 찾고 싶습니다.",
    },
    "advanced": {
        "title": "상세 필터",
        "badge": "세밀 조건 검색",
        "desc": "나이, 리그, 팀, 연봉, 출전시간, 세부 점수까지 직접 조합합니다.",
        "request": "상세 조건을 직접 설정해서 스카우팅 후보를 좁혀 보고 싶습니다.",
    },
}

POSITION_LABELS = {
    "ALL": "전체",
    "FW": "공격수 FW",
    "MF": "미드필더 MF",
    "DF": "수비수 DF",
    "GK": "골키퍼 GK",
}

PRIORITY_METRICS = [
    "공격",
    "슈팅",
    "찬스 창출",
    "전진 패스",
    "창의 패스",
    "압박",
    "수비",
    "볼 탈취",
    "빌드업",
    "공중볼/수비",
    "GK",
]

METRIC_FOCUS_LABELS = {
    "overall": "종합",
    "attack": "공격",
    "passing": "창의성/전개",
    "defense": "수비",
    "physical": "압박/활동량",
    "balanced": "균형",
}

COMPARISON_SCOPE_LABELS = {
    "same_position": "같은 포지션 기준",
    "same_league_position": "같은 리그 + 같은 포지션 기준",
    "big5": "Big 5 리그 전체 기준",
}

SCORE_FILTER_LABELS = {
    "overall_role_score_min": "최소 종합 역할 점수",
    "attack_score_min": "최소 공격 점수",
    "shooting_score_min": "최소 슈팅 점수",
    "chance_creation_score_min": "최소 찬스 창출 점수",
    "progressive_pass_score_min": "최소 전진 패스 점수",
    "creative_pass_score_min": "최소 창의 패스 점수",
    "pressing_score_min": "최소 압박 점수",
    "defensive_action_score_min": "최소 수비 행동 점수",
    "ball_winning_score_min": "최소 볼 탈취 점수",
    "build_up_score_min": "최소 빌드업 점수",
    "aerial_defense_score_min": "최소 공중볼/수비 점수",
    "goalkeeper_score_min": "최소 골키퍼 점수",
    "salary_value_score_min": "최소 연봉 가치 점수",
    "salary_efficiency_score_min": "최소 연봉 효율 점수",
    "role_fit_finisher_min": "최소 Finisher 적합도",
    "role_fit_pressing_forward_min": "최소 Pressing Forward 적합도",
    "role_fit_creative_midfielder_min": "최소 Creative Midfielder 적합도",
    "role_fit_progressive_passer_min": "최소 Progressive Passer 적합도",
    "role_fit_ball_winning_midfielder_min": "최소 Ball Winning Midfielder 적합도",
    "role_fit_ball_playing_defender_min": "최소 Ball Playing Defender 적합도",
    "role_fit_defensive_stopper_min": "최소 Defensive Stopper 적합도",
    "role_fit_shot_stopper_min": "최소 Shot Stopper 적합도",
}

SORT_LABELS = {
    "overall_role_score": "종합 역할 점수",
    "salary_value_score": "연봉 가치 점수",
    "salary_efficiency_score": "연봉 효율 점수",
    "attack_score": "공격 점수",
    "shooting_score": "슈팅 점수",
    "chance_creation_score": "찬스 창출 점수",
    "progressive_pass_score": "전진 패스 점수",
    "creative_pass_score": "창의 패스 점수",
    "pressing_score": "압박 점수",
    "defensive_action_score": "수비 행동 점수",
    "ball_winning_score": "볼 탈취 점수",
    "build_up_score": "빌드업 점수",
    "aerial_defense_score": "공중볼/수비 점수",
    "goalkeeper_score": "골키퍼 점수",
    "minutes": "출전 시간",
    "age": "나이",
    "salary_annual_gross_eur": "연봉",
    "role_fit_finisher": "Finisher 적합도",
    "role_fit_pressing_forward": "Pressing Forward 적합도",
    "role_fit_creative_midfielder": "Creative Midfielder 적합도",
    "role_fit_progressive_passer": "Progressive Passer 적합도",
    "role_fit_ball_winning_midfielder": "Ball Winning Midfielder 적합도",
    "role_fit_ball_playing_defender": "Ball Playing Defender 적합도",
    "role_fit_defensive_stopper": "Defensive Stopper 적합도",
    "role_fit_shot_stopper": "Shot Stopper 적합도",
}


SECTION_META = {
    "role_based": {
        "title": "내가 원하는 선수 찾기",
        "subtitle": "조건을 나누어 설정하고 원하는 유형의 선수를 빠르게 찾으세요.",
    },
    "value": {
        "title": "연봉 가치 진단",
        "subtitle": "한 명의 선수를 선택해 현재 연봉이 적절한지 빠르게 진단하세요.",
    },
    "similar": {
        "title": "대체 후보 찾기",
        "subtitle": "기준 선수와 유사한 대체 자원을 조건에 맞게 찾아보세요.",
    },
    "advanced": {
        "title": "상세 필터",
        "subtitle": "세부 조건을 직접 조합하여 스카우팅 대상을 정교하게 좁혀 보세요.",
    },
}


def _safe_unique_options(players, column: str) -> list[str]:
    if players.empty or column not in players.columns:
        return ["ALL"]

    values = sorted(
        str(value)
        for value in players[column].dropna().unique()
        if str(value).strip()
    )
    return ["ALL", *values]


def _player_options(players) -> list[dict[str, str]]:
    if players.empty:
        return []

    options: list[dict[str, str]] = []

    for _, row in players.iterrows():
        player_id = str(row.get("player_id", "") or row.get("player_name", ""))
        name = str(row.get("player_name", "Unknown"))
        team = str(row.get("team", "-"))
        league = str(row.get("league", "-"))
        age = row.get("age", "-")
        position = row.get("position_group", "-")

        options.append(
            {
                "value": player_id,
                "label": f"{name} · {position} · {team} · {league} · {age}세",
            }
        )

    return options


def _value_player_options(players) -> list[dict[str, str]]:
    """현재 사용 가능한 Azure 또는 로컬 모델 데이터에서 선수 목록을 만듭니다."""
    try:
        model_options = get_player_search_options("", limit=5000)

        normalized_options = []

        for option in model_options:
            player_id = str(option.get("player_id") or "")
            label = str(option.get("label") or "")

            if not player_id or not label:
                continue

            normalized_options.append(
                {
                    "value": player_id,
                    "label": label,
                }
            )

        if normalized_options:
            return normalized_options

    except Exception as exc:
        st.caption("모델용 선수 목록을 불러오지 못해 기본 선수 목록을 사용합니다.")
        if is_development_mode():
            with st.expander("개발자 정보 · 선수 목록 로딩 오류", expanded=False):
                st.exception(exc)

    return _player_options(players)


def _dict_option_label(options: list[dict[str, str]], value: str) -> str:
    for option in options:
        if option.get("value") == value:
            return option.get("label", value)

    return value


def _normalize_range(min_value: int, max_value: int, lower: int, upper: int) -> tuple[int, int]:
    min_value = max(lower, min(int(min_value), upper))
    max_value = max(lower, min(int(max_value), upper))
    if min_value > max_value:
        min_value, max_value = max_value, min_value
    return min_value, max_value


def _render_range_slider_with_inputs(
    label: str,
    lower: int,
    upper: int,
    default: tuple[int, int],
    key_prefix: str,
    step: int = 1,
) -> tuple[int, int]:
    """슬라이더와 숫자 입력을 양방향 동기화하되 widget default/session_state 충돌을 피합니다."""
    slider_key = f"{key_prefix}_slider"
    min_input_key = f"{key_prefix}_input_min"
    max_input_key = f"{key_prefix}_input_max"

    # 위젯이 만들어지기 전에 각 위젯의 session_state만 한 번 초기화합니다.
    # 이후 위젯에는 value=를 넘기지 않아 Streamlit 경고가 발생하지 않습니다.
    if slider_key not in st.session_state:
        initial = _normalize_range(default[0], default[1], lower, upper)
        st.session_state[slider_key] = initial

    if min_input_key not in st.session_state or max_input_key not in st.session_state:
        current_min, current_max = _normalize_range(
            st.session_state[slider_key][0],
            st.session_state[slider_key][1],
            lower,
            upper,
        )
        st.session_state[min_input_key] = current_min
        st.session_state[max_input_key] = current_max

    def _sync_from_slider() -> None:
        selected_min, selected_max = _normalize_range(
            st.session_state[slider_key][0],
            st.session_state[slider_key][1],
            lower,
            upper,
        )
        st.session_state[min_input_key] = selected_min
        st.session_state[max_input_key] = selected_max

    def _sync_from_inputs() -> None:
        selected_min, selected_max = _normalize_range(
            st.session_state[min_input_key],
            st.session_state[max_input_key],
            lower,
            upper,
        )
        st.session_state[min_input_key] = selected_min
        st.session_state[max_input_key] = selected_max
        st.session_state[slider_key] = (selected_min, selected_max)

    st.slider(
        label,
        min_value=lower,
        max_value=upper,
        step=step,
        key=slider_key,
        on_change=_sync_from_slider,
    )

    c1, c2, c3 = st.columns([1, 0.16, 1])
    with c1:
        st.number_input(
            f"{label} 최소값",
            min_value=lower,
            max_value=upper,
            step=step,
            key=min_input_key,
            on_change=_sync_from_inputs,
            label_visibility="collapsed",
        )
    with c2:
        st.markdown('<div class="range-divider">~</div>', unsafe_allow_html=True)
    with c3:
        st.number_input(
            f"{label} 최대값",
            min_value=lower,
            max_value=upper,
            step=step,
            key=max_input_key,
            on_change=_sync_from_inputs,
            label_visibility="collapsed",
        )

    selected_min, selected_max = _normalize_range(
        st.session_state[min_input_key],
        st.session_state[max_input_key],
        lower,
        upper,
    )
    return int(selected_min), int(selected_max)


def _inject_search_styles() -> None:
    """Scout Search 전용 스타일은 scout_search.css에서 관리합니다."""
    return


def _render_section_header(number: int, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-badge">{number}</div>
            <div class="section-title-wrap">
                <h3>{html.escape(title)}</h3>
                <p>{html.escape(subtitle)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_mode_header(search_type: str) -> None:
    meta = SECTION_META.get(search_type, SECTION_META["role_based"])
    st.markdown(
        f"""
        <div class="scout-form-head">
            <h2>{html.escape(meta['title'])}</h2>
            <p>{html.escape(meta['subtitle'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _select_intent() -> str:
    requested = st.query_params.get("scout_type")

    if isinstance(requested, list):
        requested = requested[0] if requested else None

    if requested in INTENTS:
        st.session_state.scout_search_type = requested

    current = st.session_state.get("scout_search_type", "role_based")

    card_html = ['<div class="scout-intent-grid">']
    for key, item in INTENTS.items():
        active = " active" if current == key else ""
        href = f"?page=scout_search&scout_type={quote(key)}"
        card_html.append(
            "<a "
            f'class="scout-intent-card{active}" '
            f'href="{href}" '
            'target="_self">'
            f'<span class="scout-intent-badge">{html.escape(item["badge"])}</span>'
            f'<span class="scout-intent-title">{html.escape(item["title"])}</span>'
            f'<span class="scout-intent-desc">{html.escape(item["desc"])}</span>'
            "</a>"
        )
    card_html.append("</div>")
    st.markdown("".join(card_html), unsafe_allow_html=True)
    return current


def _submit(conditions: dict) -> None:
    save_scout_conditions(conditions)
    move_page("scout_result")
    st.rerun()


def _render_role_based_form(players) -> dict:
    leagues = _safe_unique_options(players, "league")

    with st.container(border=True):
        _render_mode_header("role_based")

        with st.container(border=True):
            _render_section_header(1, "기본 조건", "어떤 유형의 선수를 찾고 계신가요?")
            c1, c2 = st.columns(2)
            with c1:
                position_group = st.selectbox(
                    "포지션 그룹",
                    options=["ALL", "FW", "MF", "DF", "GK"],
                    format_func=lambda key: POSITION_LABELS.get(key, key),
                    key="role_position_group",
                )
            with c2:
                role_options = get_role_options(position_group)
                role_values = [option["value"] for option in role_options] or ["Creative Midfielder"]
                role_key = st.selectbox(
                    "찾고 싶은 선수 역할 · 필수",
                    role_values,
                    key="role_key",
                )

            c3, c4 = st.columns(2)
            with c3:
                tactical_options = get_tactical_need_options(role_key)
                tactical_values = [option["value"] for option in tactical_options]
                tactical_need = st.selectbox(
                    "전술 요구 선택값",
                    ["", *tactical_values],
                    format_func=lambda value: "선택 안 함" if value == "" else value,
                    key="role_tactical_need",
                )
            with c4:
                priority_metrics = st.multiselect(
                    "중요하게 볼 능력치",
                    PRIORITY_METRICS,
                    default=[],
                    placeholder="능력치를 선택하세요 (복수 선택 가능)",
                    key="role_priority_metrics",
                )

        with st.container(border=True):
            _render_section_header(2, "세부 조건", "선수의 세부적인 조건을 설정하세요.")

            # 나이 범위는 한 줄 전체를 사용
            age_min, age_max = _render_range_slider_with_inputs(
                "나이 범위",
                15,
                45,
                (15, 45),
                "role_age_range",
            )

            # 그 아래 줄에 나머지 세부 조건을 정렬
            c6, c7, c8 = st.columns(3)
            with c6:
                max_salary = st.number_input(
                    "최대 연봉(EUR, 0은 제한 없음)",
                    min_value=0,
                    value=0,
                    step=100_000,
                    key="role_max_salary",
                )
            with c7:
                min_minutes = st.number_input(
                    "최소 출전 시간",
                    min_value=0,
                    value=0,
                    step=100,
                    key="role_min_minutes",
                )
            with c8:
                league = st.selectbox(
                    "리그",
                    leagues,
                    key="role_league",
                )

        with st.container(border=True):
            _render_section_header(3, "포함 옵션 / 결과 설정", "추가 옵션을 설정하고 원하는 결과 수를 지정하세요.")
            with st.container(key="role_options_row"):
                check1, check2, result_col = st.columns(3)
                with check1:
                    include_loan = st.checkbox(
                        "임대 선수 포함",
                        value=True,
                        key="role_include_loan",
                        width="stretch",
                    )
                with check2:
                    only_active_salary = st.checkbox(
                        "active 연봉만 사용",
                        value=False,
                        key="role_only_active_salary",
                        width="stretch",
                    )
                with result_col:
                    top_n = st.number_input(
                        "결과 개수",
                        min_value=1,
                        max_value=100,
                        value=20,
                        step=1,
                        key="role_top_n",
                    )


    return {
        "search_type": "role_based",
        "intent_label": INTENTS["role_based"]["title"],
        "request": INTENTS["role_based"]["request"],
        "position_group": position_group,
        "role_key": role_key,
        "tactical_need": tactical_need,
        "priority_metrics": priority_metrics,
        "age_min": None if age_min == 15 else int(age_min),
        "age_max": None if age_max == 45 else int(age_max),
        "max_salary": None if int(max_salary) <= 0 else int(max_salary),
        "min_minutes": None if int(min_minutes) <= 0 else int(min_minutes),
        "league": league,
        "include_loan": bool(include_loan),
        "only_active_salary": bool(only_active_salary),
        "top_n": int(top_n),
        "note": "",
    }


def _render_value_form(players) -> dict:
    options = _value_player_options(players)

    if not options:
        st.error("선수 데이터가 비어 있습니다. data/processed의 스카우터 CSV를 확인해 주세요.")
        return {
            "search_type": "value",
            "intent_label": INTENTS["value"]["title"],
        }

    labels = [option["label"] for option in options]
    label_to_value = {option["label"]: option["value"] for option in options}

    with st.container(border=True):
        _render_mode_header("value")
        with st.container(border=True):
            _render_section_header(1, "기본 조건", "연봉 가치를 진단할 선수를 선택하세요.")
            selected_label = st.selectbox(
                "평가할 선수 · 필수",
                labels,
                key="value_player_label",
            )
            st.markdown(
                '<div class="scout-mini-caption">Azure가 연결되어 있으면 Azure 데이터를 사용하고, 연결되지 않으면 프로젝트 내부 ONNX/PKL 모델을 사용합니다.</div>',
                unsafe_allow_html=True,
            )

    return {
        "search_type": "value",
        "intent_label": INTENTS["value"]["title"],
        "request": INTENTS["value"]["request"],
        "player_id": label_to_value[selected_label],
        "player_label": selected_label,
        "metric_focus": "model",
        "comparison_scope": "model_dataset",
        "min_minutes": None,
        "note": "",
    }


def _render_similar_form(players) -> dict:
    options = _player_options(players)

    if not options:
        st.error("선수 데이터가 비어 있습니다. data/processed/scout_player_view_2526.csv를 확인해 주세요.")
        return {
            "search_type": "similar",
            "intent_label": INTENTS["similar"]["title"],
        }

    labels = [option["label"] for option in options]
    label_to_value = {option["label"]: option["value"] for option in options}
    focus_options = get_similarity_focus_options()
    scope_options = get_position_scope_options()
    leagues = _safe_unique_options(players, "league")

    with st.container(border=True):
        _render_mode_header("similar")

        with st.container(border=True):
            _render_section_header(1, "기본 조건", "기준 선수와 유사도 기준을 설정하세요.")
            selected_label = st.selectbox(
                "기준 선수 · 필수",
                labels,
                key="similar_base_player_label",
            )
            c1, c2 = st.columns(2)
            with c1:
                similarity_focus = st.selectbox(
                    "유사도 기준",
                    [option["value"] for option in focus_options],
                    format_func=lambda value: _dict_option_label(focus_options, value),
                    key="similarity_focus",
                )
            with c2:
                position_scope = st.selectbox(
                    "포지션 탐색 범위",
                    [option["value"] for option in scope_options],
                    format_func=lambda value: _dict_option_label(scope_options, value),
                    key="similar_position_scope",
                )

        with st.container(border=True):
            _render_section_header(2, "세부 조건", "후보 범위를 좁힐 조건을 설정하세요.")
            c3, c4 = st.columns(2)
            with c3:
                age_limit = st.selectbox(
                    "최대 나이",
                    [0, 23, 26, 30],
                    format_func=lambda value: "제한 없음" if value == 0 else f"U{value}",
                    key="similar_age_limit",
                )
            with c4:
                max_salary = st.number_input(
                    "최대 연봉(EUR, 0은 제한 없음)",
                    min_value=0,
                    value=0,
                    step=100_000,
                    key="similar_max_salary",
                )

            c5, c6 = st.columns(2)
            with c5:
                min_minutes = st.number_input(
                    "최소 출전 시간",
                    min_value=0,
                    value=700,
                    step=100,
                    key="similar_min_minutes",
                )
            with c6:
                league = st.selectbox(
                    "리그",
                    leagues,
                    key="similar_league",
                )

        with st.container(border=True):
            _render_section_header(3, "결과 설정", "탐색 결과에서 확인할 후보 수를 지정하세요.")
            top_n = st.number_input(
                "결과 개수",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
                key="similar_top_n",
            )

    return {
        "search_type": "similar",
        "intent_label": INTENTS["similar"]["title"],
        "request": INTENTS["similar"]["request"],
        "base_player_id": label_to_value[selected_label],
        "base_player_label": selected_label,
        "similarity_focus": similarity_focus,
        "position_scope": position_scope,
        "league": league,
        "age_max": None if age_limit == 0 else int(age_limit),
        "max_salary": None if int(max_salary) <= 0 else int(max_salary),
        "min_minutes": int(min_minutes),
        "top_n": int(top_n),
        "note": "",
    }


def _render_advanced_form(players) -> dict:
    schema = get_advanced_filter_schema(
        players.to_dict("records") if not players.empty else []
    )
    score_filter_keys = [item["key"] for item in schema.get("score_filters", [])]

    with st.container(border=True):
        _render_mode_header("advanced")

        with st.container(border=True):
            _render_section_header(1, "기본 조건", "포지션, 리그, 팀 기준을 먼저 설정하세요.")
            c1, c2, c3 = st.columns(3)
            with c1:
                position_group = st.selectbox(
                    "포지션 그룹",
                    schema["position_group"]["options"],
                    format_func=lambda key: POSITION_LABELS.get(key, key),
                    key="advanced_position_group",
                )
            with c2:
                league = st.selectbox(
                    "리그",
                    schema["league"]["options"],
                    key="advanced_league",
                )
            with c3:
                team = st.selectbox(
                    "팀",
                    schema["team"]["options"],
                    key="advanced_team",
                )

        with st.container(border=True):
            _render_section_header(2, "세부 조건", "나이, 연봉, 출전 시간과 상태 조건을 설정하세요.")
            c4, c5 = st.columns(2)
            with c4:
                age_min, age_max = _render_range_slider_with_inputs(
                    "나이 범위",
                    15,
                    45,
                    (15, 45),
                    "advanced_age_range",
                )
            with c5:
                salary_min, salary_max = _render_range_slider_with_inputs(
                    "연봉 범위(EUR)",
                    0,
                    30_000_000,
                    (0, 30_000_000),
                    "advanced_salary_range",
                    step=100_000,
                )

            c6, c7 = st.columns(2)
            with c6:
                minutes_min = st.number_input(
                    "최소 출전 시간",
                    min_value=0,
                    value=int(schema["minutes_min"].get("default", 700)),
                    step=100,
                    key="advanced_minutes_min",
                )
            with c7:
                salary_value_status = st.selectbox(
                    "연봉 가치 상태",
                    schema["salary_value_status"]["options"],
                    key="advanced_salary_value_status",
                )

        with st.container(border=True):
            _render_section_header(3, "점수 / 결과 설정", "포함 조건, 점수 필터, 정렬 방식과 결과 수를 설정하세요.")
            check1, check2 = st.columns(2, gap="small")
            with check1:
                salary_available_only = st.checkbox(
                    "연봉 확인 선수만",
                    value=bool(schema["salary_available_only"].get("default", False)),
                    key="advanced_salary_available_only",
                    width="stretch",
                )
            with check2:
                score_available_only = st.checkbox(
                    "점수 계산 가능 선수만",
                    value=bool(schema["score_available_only"].get("default", True)),
                    key="advanced_score_available_only",
                    width="stretch",
                )

            selected_score_keys = st.multiselect(
                "적용할 점수 필터",
                score_filter_keys,
                default=[],
                format_func=lambda key: SCORE_FILTER_LABELS.get(key, key),
                placeholder="적용할 점수 필터를 선택하세요",
                key="advanced_selected_score_keys",
            )

            score_values: dict[str, int] = {}
            for key in selected_score_keys:
                score_values[key] = st.slider(
                    SCORE_FILTER_LABELS.get(key, key),
                    0,
                    100,
                    60,
                    key=f"advanced_{key}",
                )

            c8, c9, c10 = st.columns(3)
            with c8:
                sort_by = st.selectbox(
                    "정렬 기준",
                    schema["sort_by"]["options"],
                    format_func=lambda key: SORT_LABELS.get(key, key),
                    key="advanced_sort_by",
                )
            with c9:
                sort_direction = st.selectbox(
                    "정렬 방향",
                    ["desc", "asc"],
                    format_func=lambda value: "높은 순" if value == "desc" else "낮은 순",
                    key="advanced_sort_direction",
                )
            with c10:
                top_n = st.number_input(
                    "결과 개수",
                    min_value=1,
                    max_value=100,
                    value=50,
                    step=5,
                    key="advanced_top_n",
                )

    return {
        "search_type": "advanced",
        "intent_label": INTENTS["advanced"]["title"],
        "request": INTENTS["advanced"]["request"],
        "position_group": position_group,
        "league": league,
        "team": team,
        "age_min": None if age_min == 15 else int(age_min),
        "age_max": None if age_max == 45 else int(age_max),
        "salary_min": None if salary_min == 0 else int(salary_min),
        "salary_max": None if salary_max == 30_000_000 else int(salary_max),
        "minutes_min": int(minutes_min),
        "salary_available_only": bool(salary_available_only),
        "score_available_only": bool(score_available_only),
        "salary_value_status": salary_value_status,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
        "top_n": int(top_n),
        "note": "",
        **score_values,
    }


def _submit_button_label(search_type: str) -> str:
    return {
        "role_based": "후보 탐색 시작",
        "value": "연봉 가치 진단 시작",
        "similar": "대체 후보 탐색 시작",
        "advanced": "상세 필터 검색 시작",
    }.get(search_type, "검색 시작")


def _render_summary(conditions: dict) -> None:
    search_type = conditions.get("search_type")
    rows = [("탐색 목적", conditions.get("intent_label", "-"))]

    if search_type == "value":
        rows.extend([
            ("선수", conditions.get("player_label", "-")),
        ])
    elif search_type == "similar":
        focus_options = get_similarity_focus_options()
        scope_options = get_position_scope_options()
        rows.extend([
            ("기준 선수", conditions.get("base_player_label", "-")),
            ("유사도", _dict_option_label(focus_options, conditions.get("similarity_focus"))),
            ("포지션 범위", _dict_option_label(scope_options, conditions.get("position_scope"))),
            ("결과 개수", f"{conditions.get('top_n', 20)}명"),
        ])
    elif search_type == "advanced":
        rows.extend([
            ("포지션", POSITION_LABELS.get(conditions.get("position_group"), conditions.get("position_group"))),
            ("리그", conditions.get("league", "ALL")),
            ("팀", conditions.get("team", "ALL")),
            ("정렬", SORT_LABELS.get(conditions.get("sort_by"), conditions.get("sort_by"))),
            ("결과 개수", f"{conditions.get('top_n', 50)}명"),
        ])
    else:
        rows.extend([
            ("포지션", POSITION_LABELS.get(conditions.get("position_group"), conditions.get("position_group"))),
            ("역할", conditions.get("role_key", "-")),
            ("전술 요구", conditions.get("tactical_need") or "선택 안 함"),
            ("결과 개수", f"{conditions.get('top_n', 20)}명"),
        ])

    row_html = "".join(
        f"""
        <div class="summary-row">
            <span>{html.escape(str(label))}</span>
            <b>{html.escape(str(value))}</b>
        </div>
        """
        for label, value in rows
    )

    st.markdown(
        f"""
        <div class="summary-box">
            <h4>선택된 조건 미리보기</h4>
            <div class="summary-subtext">설정한 조건으로 어떤 선수를 찾을지 확인하세요.</div>
            <div class="summary-rows">{row_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    st.session_state.current_page = "scout_search"
    st.session_state.user_mode = "scout"

    _inject_search_styles()
    init_scout_state()
    st.session_state.setdefault("scout_search_type", "role_based")

    page_title(
        "Scout Center",
        "스카우팅 목적에 따라 조건을 설정하고 결과를 확인할 수 있습니다.",
    )

    current = _select_intent()
    players = load_scout_players()

    left, right = st.columns([1.88, 0.78], gap="large")

    with left:
        if current == "value":
            conditions = _render_value_form(players)
        elif current == "similar":
            conditions = _render_similar_form(players)
        elif current == "advanced":
            conditions = _render_advanced_form(players)
        else:
            conditions = _render_role_based_form(players)

    with right:
        _render_summary(conditions)
        st.markdown("<div style='height: 0.85rem;'></div>", unsafe_allow_html=True)

        disabled = (
            conditions.get("search_type") in {"value", "similar"}
            and not (
                conditions.get("player_id") or conditions.get("base_player_id")
            )
        )

        if st.button(
            _submit_button_label(str(conditions.get("search_type"))),
            type="primary",
            use_container_width=True,
            disabled=disabled,
        ):
            _submit(conditions)

        st.markdown(
            '<div class="summary-helper">설정한 조건에 맞는 결과를 바로 확인할 수 있습니다.</div>',
            unsafe_allow_html=True,
        )
