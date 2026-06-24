from __future__ import annotations

import pandas as pd
import streamlit as st

from src.coach.formations import FORMATIONS
from src.coach.lineup import recommend_best_formation, recommend_for_formation
from src.state import reset_lineup, set_formation, set_lineup


def render_squad_toolbar(players: pd.DataFrame) -> None:
    st.markdown("<div class='toolbar-label'>포메이션</div>", unsafe_allow_html=True)

    formations = list(FORMATIONS.keys())
    cols = st.columns([1, 1, 1, 1, 1, 1.5, 2.0, 1.4])

    for idx, formation in enumerate(formations):
        button_type = "primary" if st.session_state.formation == formation else "secondary"

        if cols[idx].button(formation, type=button_type, use_container_width=True):
            set_formation(formation)
            st.rerun()

    if cols[5].button("✨ AI 자동 추천", type="primary", use_container_width=True):
        formation, lineup, _ = recommend_best_formation(players)
        set_formation(formation)
        set_lineup(lineup)
        st.success(f"AI가 {formation} 포메이션을 선택했습니다.")
        st.rerun()

    if cols[6].button("🛠 선택 포메이션 기준 추천", use_container_width=True):
        lineup = recommend_for_formation(players, st.session_state.formation)
        set_lineup(lineup)
        st.success(f"{st.session_state.formation} 기준 추천 라인업을 생성했습니다.")
        st.rerun()

    if cols[7].button("↻ 라인업 초기화", use_container_width=True):
        reset_lineup()
        st.rerun()