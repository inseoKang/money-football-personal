from __future__ import annotations

import streamlit as st

from components.layout import page_title


def _mode_card_html(
    *,
    page: str,
    badge: str,
    title: str,
    description: str,
    features: list[str],
    note: str,
) -> str:
    feature_html = "".join(
        f"<div class='feature-pill'>{feature}</div>"
        for feature in features
    )

    return f"""
    <a class="mode-card mode-card-link" href="?page={page}" target="_self" aria-label="{title} 모드로 이동">
      <div class="mode-card-heading">
        <h3>{title}</h3>
        <span class="mode-badge">{badge}</span>
      </div>
      <p>{description}</p>

      <div class="feature-list">
        {feature_html}
      </div>

      <div class="mode-note">
        {note}
      </div>
    </a>
    """


def render() -> None:
    st.markdown('<span class="home-page-marker" aria-hidden="true"></span>', unsafe_allow_html=True)

    page_title(
        "Money Football",
        "감독과 스카우터를 위한 데이터 기반 축구 선수 분석 서비스입니다.",
    )

    st.markdown(
        """
        <div class="home-hero">
          <div class="hero-kicker">⚽ AI Football Decision Support</div>
          <h2>데이터로 라인업을 짜고,<br/>선수 시장을 더 빠르게 읽습니다.</h2>
          <p>
            <span class="hero-highlight">Money Football</span>은 축구 감독과 스카우터가
            선수 능력치, 포지션 적합도, 팀 밸런스, 시장 후보군을 한 화면에서 비교하고
            더 나은 의사결정을 할 수 있도록 돕는 분석 서비스입니다.
          </p>

          <div class="home-summary-grid">
            <div class="summary-item">
              <strong>Lineup Build</strong>
              <span>포메이션 기반 선수 배치와 AI 추천</span>
            </div>
            <div class="summary-item">
              <strong>VS Analysis</strong>
              <span>상대 라리가 팀과 전력 차이 비교</span>
            </div>
            <div class="summary-item">
              <strong>Scout Search</strong>
              <span>조건 기반 후보 탐색과 시장 분석</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='mode-grid-spacer'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            _mode_card_html(
                page="coach_squad",
                badge="Coach Mode",
                title="감독용",
                description=(
                    "Barcelona 선수단을 기준으로 최적 라인업을 구성하고, "
                    "상대 팀과의 전력 차이를 비교합니다."
                ),
                features=[
                    "내 스쿼드 구성",
                    "AI 추천 라인업",
                    "VS 스쿼드 비교",
                    "선수단 대시보드",
                ],
                note=(
                    "포메이션별 적합도와 팀 종합 점수를 확인하면서 "
                    "직접 라인업을 조정할 수 있습니다."
                ),
            ),
            unsafe_allow_html=True,
        )


    with col2:
        st.markdown(
            _mode_card_html(
                page="scout_search",
                badge="Scout Mode",
                title="스카우터용",
                description=(
                    "전체 선수 데이터를 기반으로 조건에 맞는 후보군을 탐색하고, "
                    "선수 가치와 시장성을 비교합니다."
                ),
                features=[
                    "역할 기반 탐색",
                    "유사 선수 탐색",
                    "가성비 선수 탐색",
                    "시장 대시보드",
                ],
                note=(
                    "포지션, 역할, 능력치 조건을 조합해 후보 선수를 "
                    "빠르게 좁힐 수 있습니다."
                ),
            ),
            unsafe_allow_html=True,
        )

