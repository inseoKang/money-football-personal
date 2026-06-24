from __future__ import annotations

import html

import streamlit as st


def _safe_int(value) -> int:
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return 0


def metric_bar(label: str, value) -> None:
    score = _safe_int(value)

    st.markdown(
        f"""
        <div class="metric-row">
          <div class="metric-label">
            <span>{html.escape(label)}</span>
            <b>{score}</b>
          </div>
          <div class="bar">
            <div style="width:{score}%"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def grade_card(score, grade: str) -> None:
    score_value = _safe_int(score)

    st.markdown(
        f"""
        <div class="grade-card">
          <div>
            <div class="muted">팀 종합 점수</div>
            <div class="big-score">{score_value}<span>/100</span></div>
          </div>
          <div class="grade-badge">{html.escape(str(grade))}<small>GRADE</small></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics_panel(
    metrics: dict,
    formation: str,
    ai_comment: str = "",
    warnings: list[str] | None = None,
    *,
    title: str = "⚽ AI 감독 코멘트",
) -> None:
    warnings = warnings or []

    with st.container(border=True):
        st.markdown(f"#### {title}")

        if metrics.get("team_score", 0) == 0:
            st.write(
                "아직 라인업이 비어 있습니다. 포메이션을 선택하고 선수를 배치하거나 AI 추천을 실행해 보세요."
            )
        elif ai_comment:
            st.write(ai_comment)
        else:
            st.write(
                f"현재 {formation} 라인업은 팀 종합 점수 {metrics.get('team_score', 0)}점입니다. "
                "포지션 적합도와 좌우 밸런스를 함께 고려한 추천 결과입니다."
            )

        if warnings:
            with st.expander("라인업 경고 확인"):
                for warning in warnings:
                    st.caption(f"- {warning}")

    grade_card(metrics.get("team_score", 0), metrics.get("grade", "C"))

    with st.container(border=True):
        st.markdown("#### 세부 지표")
        metric_bar("공격 기대값", metrics.get("attack", 0))
        metric_bar("중원 장악력", metrics.get("midfield", 0))
        metric_bar("수비 안정성", metrics.get("defense", 0))
        metric_bar("골키퍼 안정성", metrics.get("keeper", 0))
        metric_bar("포지션 적합도", metrics.get("position_fit", 0))
        metric_bar("좌우 밸런스", metrics.get("balance", 0))
        metric_bar("선수 시너지", metrics.get("synergy", 0))