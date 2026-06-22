from __future__ import annotations

import streamlit as st

from components.layout import page_title
from components.navigation import set_mode


def render() -> None:
    page_title(
        "Money Football",
        "감독과 스카우터를 위한 데이터 기반 축구 선수 분석 서비스입니다.",
    )

    st.markdown(
        """
        <div class="hero-panel">
          <h2>어떤 목적으로 접속하시나요?</h2>
          <p>
            감독은 보유 선수 기반 최적 라인업과 상대 국가별 대응 스쿼드를 확인할 수 있고,
            스카우터는 선수 데이터 분석, 검색, 버블 차트를 통해 저평가 선수를 탐색할 수 있습니다.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="mode-card">
              <div class="mode-icon">🧠</div>
              <h3>감독용</h3>
              <p>내 선수들로 최적의 포메이션과 선발 라인업을 구성합니다.</p>
              <ul>
                <li>내 스쿼드 구성</li>
                <li>AI 추천 라인업</li>
                <li>상대 국가별 VS 스쿼드</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("감독용으로 시작하기", type="primary", use_container_width=True):
            set_mode("coach")
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="mode-card">
              <div class="mode-icon">🔎</div>
              <h3>스카우터용</h3>
              <p>선수 능력치, 시장가치, 연봉 데이터를 비교해 선수를 탐색합니다.</p>
              <ul>
                <li>선수 대시보드</li>
                <li>선수 정렬/필터/검색</li>
                <li>버블 차트 기반 선수 검색</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("스카우터용으로 시작하기", type="primary", use_container_width=True):
            set_mode("scout")
            st.rerun()