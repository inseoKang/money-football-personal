from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.scout.scout_query import ROLE_SCORE_COLUMNS


SCOUT_INTENTS: dict[str, dict[str, str]] = {
    "role_based": {
        "title": "역할 기반 탐색",
        "description": "우리 팀에 필요한 역할을 정하고 그 역할에 맞는 후보를 찾습니다.",
        "example": "창의형 미드필더, 압박형 공격수",
        "default_request": "창의형 미드필더가 필요합니다. 전진 패스와 찬스 메이킹이 좋고, 연봉 부담이 크지 않은 선수를 찾고 싶습니다.",
        "default_position": "MF",
        "default_role": "Creative Midfielder",
    },
    "similar": {
        "title": "유사 선수 탐색",
        "description": "특정 선수와 비슷한 스타일의 대체 후보를 찾습니다.",
        "example": "손흥민과 비슷한 공격수",
        "default_request": "기준 선수와 비슷한 스타일의 대체 후보를 찾고 싶습니다. 공격 기여도와 역할 유사성이 중요합니다.",
        "default_position": "FW",
        "default_role": "Finisher",
    },
    "value": {
        "title": "가성비 선수 탐색",
        "description": "현재 연봉이나 시장가치 대비 성능이 좋은 저평가 선수를 찾습니다.",
        "example": "연봉 대비 성능이 좋은 선수",
        "default_request": "연봉 대비 성능이 좋은 저평가 선수를 찾고 싶습니다. 즉시 활용 가능한 후보를 우선으로 봅니다.",
        "default_position": "ALL",
        "default_role": "Progressive Passer",
    },
    "prospect": {
        "title": "유망주 탐색",
        "description": "어린 나이와 성장 가능성을 기준으로 후보를 찾습니다.",
        "example": "21세 이하, 출전 경험 있는 선수",
        "default_request": "어린 나이와 성장 가능성을 가진 유망주를 찾고 싶습니다. 출전 경험이 어느 정도 있는 선수를 우선으로 봅니다.",
        "default_position": "ALL",
        "default_role": "Creative Midfielder",
    },
}


POSITION_OPTIONS = {
    "ALL": "ALL - 전체",
    "FW": "FW - 공격수",
    "MF": "MF - 미드필더",
    "DF": "DF - 수비수",
    "GK": "GK - 골키퍼",
}

TACTICAL_NEEDS = [
    "찬스 메이킹과 전진 패스가 필요함",
    "높은 압박과 활동량이 필요함",
    "박스 안 득점력이 필요함",
    "빌드업 안정성이 필요함",
    "공중볼과 수비 안정성이 필요함",
]

ROLE_OPTIONS = list(ROLE_SCORE_COLUMNS.keys())

PRIORITY_METRICS = ["공격", "패스", "중원 전개", "수비", "압박", "피지컬", "연봉 효율"]
LEAGUE_OPTIONS = ["ALL", "K League 1", "K League 2", "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]

AGE_PRESETS = {
    "u23": {"label": "23세 이하", "age_min": 15, "age_max": 23},
    "u26": {"label": "26세 이하", "age_min": 15, "age_max": 26},
    "u30": {"label": "30세 이하", "age_min": 15, "age_max": 30},
    "all": {"label": "제한 없음", "age_min": 15, "age_max": 45},
}

BUDGET_PRESETS = {
    "1m": {"label": "€1M 이하", "max_salary": 1_000_000},
    "3m": {"label": "€3M 이하", "max_salary": 3_000_000},
    "5m": {"label": "€5M 이하", "max_salary": 5_000_000},
    "all": {"label": "제한 없음", "max_salary": 0},
}


def get_intent_label(intent_key: str) -> str:
    return SCOUT_INTENTS.get(intent_key, SCOUT_INTENTS["role_based"])["title"]


def get_age_label(age_key: str) -> str:
    return AGE_PRESETS.get(age_key, AGE_PRESETS["u26"])["label"]


def get_budget_label(budget_key: str) -> str:
    return BUDGET_PRESETS.get(budget_key, BUDGET_PRESETS["3m"])["label"]


def get_position_label(position_key: str) -> str:
    return POSITION_OPTIONS.get(position_key, position_key)


def render_intent_cards() -> None:
    cols = st.columns(4)

    for index, (intent_key, intent) in enumerate(SCOUT_INTENTS.items()):
        is_active = st.session_state.get("scout_search_type", "role_based") == intent_key

        with cols[index]:
            with st.container(border=True):
                st.markdown(f"### {intent['title']}")
                st.write(intent["description"])
                st.caption(f"예: {intent['example']}")

                button_label = "선택됨" if is_active else "선택하기"
                if st.button(button_label, key=f"scout_intent_{intent_key}", use_container_width=True):
                    st.session_state.scout_search_type = intent_key
                    st.session_state.scout_request = intent["default_request"]
                    st.session_state.scout_position_group = intent["default_position"]
                    st.session_state.scout_role_key = intent["default_role"]
                    st.rerun()


def render_scout_flow_steps() -> None:
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### STEP 1")
        st.write("목적 선택")
        st.caption("처음에는 선수 리스트보다 어떤 선수를 찾는지 먼저 정합니다.")

    with c2:
        st.markdown("#### STEP 2")
        st.write("요청서 보완")
        st.caption("역할, 전술 요구사항, 현실 조건을 구체화합니다.")

    with c3:
        st.markdown("#### STEP 3")
        st.write("후보 생성")
        st.caption("역할 적합도, 가치 점수, 리스크를 기준으로 후보를 확인합니다.")


def render_condition_summary(conditions: dict[str, Any]) -> None:
    st.markdown("### 현재 검색 기준 요약")
    st.write(conditions.get("request") or conditions.get("note") or "요청 내용이 없습니다.")

    c1, c2, c3, c4 = st.columns(4)
    c1.caption("탐색 목적")
    c1.write(conditions.get("intent_label", get_intent_label(conditions.get("search_type", "role_based"))))
    c2.caption("포지션")
    c2.write(get_position_label(conditions.get("position_group", "ALL")))
    c3.caption("나이")
    c3.write(f"{conditions.get('age_min', 15)}~{conditions.get('age_max', 45)}세")
    c4.caption("예산")
    max_salary = int(conditions.get("max_salary", 0) or 0)
    c4.write("제한 없음" if max_salary <= 0 else f"€{max_salary:,} 이하")

    c5, c6, c7 = st.columns(3)
    c5.caption("역할")
    c5.write(conditions.get("role_key", "-"))
    c6.caption("전술 요구")
    c6.write(conditions.get("tactical_need", "-"))
    c7.caption("최소 출전시간")
    c7.write(f"{int(conditions.get('min_minutes', 0) or 0):,}분")


def render_candidate_card(candidate: dict[str, Any], index: int, selected_index: int) -> None:
    is_selected = index == selected_index

    with st.container(border=True):
        st.markdown(f"**{candidate.get('name', '-')}**")
        st.caption(
            f"{candidate.get('club', '-')} · {candidate.get('nation', '-')} · "
            f"{candidate.get('age_label', candidate.get('age', '나이 정보 없음'))} · {candidate.get('position', '-')}"
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Fit", int(candidate.get("fit", 0)))
        c2.metric("Value", int(candidate.get("value", 0)))
        c3.metric("OVR", int(candidate.get("overall", 0)))

        st.write(candidate.get("comment", "후보 선수입니다."))

        button_label = "선택됨" if is_selected else "이 선수 보기"
        if st.button(button_label, key=f"select_scout_candidate_{index}", use_container_width=True):
            st.session_state.selected_scout_candidate_index = index
            st.rerun()


def render_candidate_map(candidates: list[dict[str, Any]], selected_index: int) -> None:
    if not candidates:
        st.info("표시할 후보가 없습니다.")
        return

    df = pd.DataFrame(candidates).copy()
    df["selected"] = ["선택됨" if i == selected_index else "후보" for i in range(len(df))]

    st.markdown("#### 선수 위치 맵")
    st.caption("가로축은 역할 적합도, 세로축은 가치 점수입니다. 후보 리스트에서 선택한 선수는 상세 분석에 반영됩니다.")

    st.scatter_chart(
        df,
        x="fit",
        y="value",
        size="overall",
        color="selected",
        use_container_width=True,
    )


def render_candidate_detail(candidate: dict[str, Any]) -> None:
    st.markdown("### 선수 세부 분석")

    tab1, tab2, tab3 = st.tabs(["요약", "세부 스탯", "코멘트·리스크"])

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("역할 적합도", int(candidate.get("fit", 0)))
        c2.metric("가치 점수", int(candidate.get("value", 0)))
        c3.metric("종합 점수", int(candidate.get("overall", 0)))
        c4.metric("현재 연봉", candidate.get("salary_label", "정보 없음"))

        st.info(candidate.get("comment", "후보 선수입니다."))

    with tab2:
        st.markdown("#### 주요 능력치")
        for label, key in [
            ("공격", "attack_score"),
            ("중원", "midfield_score"),
            ("수비", "defense_score"),
            ("속도", "pace_score"),
            ("피지컬", "physical_score"),
            ("체력", "stamina_score"),
        ]:
            value = int(candidate.get(key, 0) or 0)
            st.progress(value / 100, text=f"{label} {value}")

    with tab3:
        strengths = candidate.get("strengths", [])
        risk = candidate.get("risk", "추가 확인 필요")

        st.markdown("#### 강점")
        if strengths:
            for strength in strengths:
                st.write(f"- {strength}")
        else:
            st.write("- 데이터 기반 강점 산출 예정")

        st.markdown("#### 리스크")
        st.warning(risk)

        st.markdown("#### 스카우터 코멘트")
        st.info(candidate.get("comment", "추가 분석이 필요합니다."))
