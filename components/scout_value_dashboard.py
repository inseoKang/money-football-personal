from __future__ import annotations

import html
from textwrap import dedent

import pandas as pd
import streamlit as st


FEATURE_LABELS = {
    "age": "나이",
    "minutes": "출전 시간",
    "starts": "선발 출전",
    "nineties": "90분 환산 출전",
    "goals": "득점",
    "assists": "도움",
    "shots": "슈팅",
    "shots_on_target": "유효 슈팅",
    "position_group": "포지션 그룹",
    "league": "리그",
    "salary_annual_gross_eur": "현재 연봉",
    "current_salary_annual_gross_eur": "현재 연봉",
    "salary_target_eur": "목표 연봉",
    "fe_log_salary_target_eur": "로그 목표 연봉",
    "fe_club_mean_salary_target_eur": "소속팀 평균 목표 연봉",
    "fe_goal_contribution": "공격 포인트",
    "overall_role_score": "종합 역할 점수",
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
    "salary_efficiency_score": "연봉 효율 점수",
    "salary_value_score": "연봉 가치 점수",
    "performance_percentile_by_position": "포지션 내 성능 백분위",
    "salary_percentile_by_position": "포지션 내 연봉 백분위",
    "salary_percentile_by_league": "리그 내 연봉 백분위",
    "minutes_percentile_by_position": "포지션 내 출전시간 백분위",
}


def _html(markup: str) -> None:
    cleaned = dedent(markup).strip()

    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


def _num(value, default: float = 0.0) -> float:
    try:
        number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(number):
            return default
        return float(number)
    except Exception:
        return default


def _fmt_money(value) -> str:
    number = _num(value, 0.0)

    if number == 0:
        return "정보 없음"

    sign = "-" if number < 0 else ""
    number = abs(number)

    if number >= 1_000_000:
        return f"{sign}€{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{sign}€{number / 1_000:.0f}K"

    return f"{sign}€{number:,.0f}"


def _fmt_number(value) -> str:
    number = _num(value, 0.0)

    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    if abs(number) >= 1_000:
        return f"{number / 1_000:.1f}K"
    if float(number).is_integer():
        return f"{int(number):,}"

    return f"{number:.3f}"


def _fmt_pct(value) -> str:
    if value in [None, ""]:
        return "-"
    return f"{_num(value):.2f}%"


def _feature_label(feature: object) -> str:
    key = str(feature or "")
    return FEATURE_LABELS.get(key, key)


def _direction_class(direction: object) -> str:
    if str(direction).lower() == "decrease":
        return "decrease"
    return "increase"


def _direction_label(direction: object) -> str:
    if str(direction).lower() == "increase":
        return "예측 연봉 상승 요인"
    if str(direction).lower() == "decrease":
        return "예측 연봉 하락 요인"
    return "영향 방향 확인 필요"


def _status_class(status: object, label: object) -> str:
    status_text = str(status or "").lower()
    label_text = str(label or "")

    if status_text == "undervalued" or "저평가" in label_text:
        return "undervalued"
    if status_text == "overvalued" or "고평가" in label_text:
        return "overvalued"
    if status_text == "fair" or "적정" in label_text:
        return "fair"

    return "unknown"


def _build_shap_dataframe(top_features: list[dict]) -> pd.DataFrame:
    shap_df = pd.DataFrame(top_features)

    if shap_df.empty:
        return shap_df

    shap_df["feature_label"] = shap_df["feature"].apply(_feature_label)
    shap_df["direction_label"] = shap_df["direction"].apply(_direction_label)
    shap_df["direction_class"] = shap_df["direction"].apply(_direction_class)
    shap_df["contribution_log_salary"] = pd.to_numeric(
        shap_df["contribution_log_salary"],
        errors="coerce",
    ).fillna(0.0)
    shap_df["abs_contribution"] = shap_df["contribution_log_salary"].abs()

    return shap_df.sort_values("abs_contribution", ascending=False).reset_index(drop=True)


def _kpi_card(label: str, value: str, caption: str = "") -> str:
    return f"""
    <div class="svd-kpi-card">
      <div class="svd-kpi-label">{html.escape(label)}</div>
      <div class="svd-kpi-value">{html.escape(str(value))}</div>
      <div class="svd-kpi-caption">{html.escape(str(caption))}</div>
    </div>
    """


def _render_header(result: dict, player_label: str) -> None:
    value_label = str(result.get("salary_value_label", "평가 불가"))
    status = result.get("salary_value_status")
    status_class = _status_class(status, value_label)

    player_name = html.escape(str(result.get("player_name", player_label)))
    team = html.escape(str(result.get("team", "-")))
    league = html.escape(str(result.get("league", "-")))
    position = html.escape(str(result.get("position_group", "-")))
    age = html.escape(str(result.get("age", "-")))
    explanation = html.escape(str(result.get("explanation", "설명 데이터가 없습니다.")))

    _html(
        f"""
        <div class="svd-hero">
          <div class="svd-hero-main">
            <div class="svd-kicker">SCOUT AI SALARY VALUE REPORT</div>
            <div class="svd-player-name">{player_name}</div>
            <div class="svd-player-meta">{team} · {league} · {position} · {age}세</div>
          </div>

          <div class="svd-status {status_class}">
            <span>가치 판단</span>
            <strong>{html.escape(value_label)}</strong>
          </div>
        </div>

        <div class="svd-explain-card">
          {explanation}
        </div>
        """
    )


def _render_salary_kpis(result: dict) -> None:
    current_salary = result.get("current_salary_annual_gross_eur")
    predicted_salary = result.get("predicted_next_salary_annual_gross_eur")
    gap = result.get("salary_gap_eur")
    gap_pct = result.get("salary_gap_pct")
    value_label = result.get("salary_value_label", "평가 불가")

    gap_caption = "예측 연봉 - 현재 연봉"
    if gap_pct not in [None, ""]:
        gap_caption = f"현재 연봉 대비 {_fmt_pct(gap_pct)}"

    kpi_html = "".join(
        [
            _kpi_card("현재 연봉", _fmt_money(current_salary), "현재 연간 총액 기준"),
            _kpi_card("예측 다음 시즌 연봉", _fmt_money(predicted_salary), "ONNX 모델 예측값"),
            _kpi_card("연봉 차액", _fmt_money(gap), gap_caption),
            _kpi_card("가치 판단", str(value_label), "저평가 · 적정 · 고평가"),
        ]
    )

    _html(
        f"""
        <div class="svd-kpi-grid">
          {kpi_html}
        </div>
        """
    )


def _render_salary_comparison(result: dict) -> None:
    current_salary = _num(result.get("current_salary_annual_gross_eur"))
    predicted_salary = _num(result.get("predicted_next_salary_annual_gross_eur"))
    gap_pct = _num(result.get("salary_gap_pct"))

    max_salary = max(current_salary, predicted_salary, 1)
    current_width = max(3, current_salary / max_salary * 100)
    predicted_width = max(3, predicted_salary / max_salary * 100)

    gap_abs = abs(gap_pct)
    gap_width = max(4, min(100, gap_abs / 80 * 100))

    gap_direction = "up" if gap_pct >= 0 else "down"
    gap_label = "예측 연봉이 더 높음" if gap_pct >= 0 else "현재 연봉이 더 높음"

    _html(
        f"""
        <div class="svd-panel">
          <div class="svd-panel-head">
            <div>
              <div class="svd-panel-title">현재 연봉 vs 모델 예측 연봉</div>
              <div class="svd-panel-desc">
                ONNX 모델이 예측한 다음 시즌 적정 연봉과 현재 연봉의 차이를 비교합니다.
              </div>
            </div>
            <div class="svd-panel-badge">{html.escape(gap_label)}</div>
          </div>

          <div class="svd-compare-row">
            <div class="svd-compare-label">현재 연봉</div>
            <div class="svd-compare-track">
              <div class="svd-compare-fill current" style="width:{current_width:.1f}%"></div>
            </div>
            <div class="svd-compare-value">{html.escape(_fmt_money(current_salary))}</div>
          </div>

          <div class="svd-compare-row">
            <div class="svd-compare-label">예측 연봉</div>
            <div class="svd-compare-track">
              <div class="svd-compare-fill predicted" style="width:{predicted_width:.1f}%"></div>
            </div>
            <div class="svd-compare-value">{html.escape(_fmt_money(predicted_salary))}</div>
          </div>

          <div class="svd-gap-meter">
            <div class="svd-gap-top">
              <span>차이율</span>
              <b>{html.escape(_fmt_pct(gap_pct))}</b>
            </div>
            <div class="svd-gap-track">
              <div class="svd-gap-fill {gap_direction}" style="width:{gap_width:.1f}%"></div>
            </div>
          </div>
        </div>
        """
    )


def _render_model_meta(result: dict) -> None:
    model_name = result.get("prediction_model_name") or "-"
    model_version = result.get("prediction_model_version") or "-"
    r2_score = result.get("prediction_r2_score")
    r2_text = "-" if r2_score in [None, ""] else str(r2_score)

    _html(
        f"""
        <div class="svd-model-card">
          <div class="svd-model-title">모델 정보</div>
          <div class="svd-model-desc">
            모델명: <b>{html.escape(str(model_name))}</b>
            · 버전: <b>{html.escape(str(model_version))}</b>
            · R2: <b>{html.escape(str(r2_text))}</b>
          </div>
          <div class="svd-model-note">
            SHAP 설명값은 모델의 <b>로그 연봉 예측값</b> 기준으로 각 지표가 예측을 높이거나 낮춘 정도를 보여줍니다.
          </div>
        </div>
        """
    )


def _render_empty_shap(reason: str) -> None:
    _html(
        f"""
        <div class="svd-empty-card">
          SHAP 설명값을 표시할 수 없습니다.<br/>
          사유: {html.escape(str(reason))}
        </div>
        """
    )


def _render_shap_dashboard(result: dict) -> None:
    shap_result = result.get("shap_explanation") or {}

    if not shap_result.get("explanation_available"):
        _render_empty_shap(str(shap_result.get("reason", "explanation_not_available")))
        return

    top_features = shap_result.get("top_features", []) or []
    shap_df = _build_shap_dataframe(top_features)

    if shap_df.empty:
        _render_empty_shap("top_features_empty")
        return

    base_value = shap_result.get("base_value_log_salary", "-")
    max_abs = max(float(shap_df["abs_contribution"].max()), 0.000001)

    increase_df = shap_df[shap_df["direction_class"] == "increase"]
    decrease_df = shap_df[shap_df["direction_class"] == "decrease"]

    top_row = shap_df.iloc[0]
    top_feature = str(top_row.get("feature_label", "-"))
    top_impact = float(top_row.get("contribution_log_salary", 0.0))

    total_up = increase_df["contribution_log_salary"].sum() if not increase_df.empty else 0.0
    total_down = decrease_df["contribution_log_salary"].sum() if not decrease_df.empty else 0.0

    summary_html = "".join(
        [
            _kpi_card("최대 영향 지표", top_feature, f"기여도 {top_impact:+.6f}"),
            _kpi_card("상승 요인", f"{len(increase_df)}개", f"합계 {total_up:+.6f}"),
            _kpi_card("하락 요인", f"{len(decrease_df)}개", f"합계 {total_down:+.6f}"),
            _kpi_card("Base log salary", str(base_value), "모델 기준 예측값"),
        ]
    )

    feature_rows_html = ""

    for index, row in shap_df.iterrows():
        direction_class = str(row.get("direction_class", "increase"))
        contribution = float(row.get("contribution_log_salary", 0.0))
        width = max(6, min(100, abs(contribution) / max_abs * 100))

        feature_label = html.escape(str(row.get("feature_label", "-")))
        feature_key = html.escape(str(row.get("feature", "-")))
        value_text = html.escape(_fmt_number(row.get("value")))
        contribution_text = html.escape(f"{contribution:+.6f}")
        direction_text = html.escape(str(row.get("direction_label", "-")))

        rank = index + 1

        feature_rows_html += f"""
        <div class="svd-shap-row">
          <div class="svd-rank">{rank}</div>

          <div class="svd-shap-body">
            <div class="svd-shap-top">
              <div>
                <div class="svd-shap-name">{feature_label}</div>
                <div class="svd-shap-meta">
                  {feature_key} · 값 {value_text} · 기여도 {contribution_text}
                </div>
              </div>
              <div class="svd-shap-pill {direction_class}">{direction_text}</div>
            </div>

            <div class="svd-shap-track">
              <div class="svd-shap-fill {direction_class}" style="width:{width:.1f}%"></div>
            </div>
          </div>
        </div>
        """

    _html(
        f"""
        <div class="svd-shap-dashboard">
          <div class="svd-panel-head">
            <div>
              <div class="svd-panel-title">SHAP 예측 영향도 분석</div>
              <div class="svd-panel-desc">
                모델이 이 선수의 다음 시즌 연봉을 예측할 때 가장 크게 참고한 지표입니다.
              </div>
            </div>
            <div class="svd-panel-badge">Top {len(shap_df)} Features</div>
          </div>

          <div class="svd-shap-summary-grid">
            {summary_html}
          </div>

          <div class="svd-shap-board">
            {feature_rows_html}
          </div>
        </div>
        """
    )

    with st.expander("SHAP 상세 데이터 보기", expanded=False):
        display_df = shap_df[
            [
                "feature_label",
                "feature",
                "value",
                "contribution_log_salary",
                "direction_label",
            ]
        ].rename(
            columns={
                "feature_label": "지표명",
                "feature": "원본 컬럼",
                "value": "값",
                "contribution_log_salary": "로그 연봉 기여도",
                "direction_label": "영향 방향",
            }
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )


def render_salary_value_dashboard(result: dict, player_label: str = "") -> None:
    _render_header(result, player_label)
    _render_salary_kpis(result)
    _render_salary_comparison(result)
    _render_model_meta(result)
    _render_shap_dashboard(result)