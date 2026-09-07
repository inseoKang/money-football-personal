from __future__ import annotations

import html
from textwrap import dedent
from typing import Iterable

import pandas as pd
import streamlit as st

from components.layout import page_title
from components.navigation import move_page
from components.scout_value_dashboard import render_salary_value_dashboard
from src.data_loader import load_scout_players
from src.runtime import is_development_mode
from src.scout.scout_query import (
    advanced_search_players,
    evaluate_player_value,
    find_role_based_players,
    find_similar_players,
)
from src.scout.scout_state import get_scout_conditions


DISPLAY_COLUMNS = {
    "player_name": "선수",
    "team": "팀",
    "league": "리그",
    "position": "포지션",
    "position_group": "그룹",
    "age": "나이",
    "minutes": "출전 시간",
    "salary_annual_gross_eur": "연봉(EUR)",
    "current_salary_annual_gross_eur": "현재 연봉(EUR)",
    "predicted_next_salary_annual_gross_eur": "예측 다음 시즌 연봉(EUR)",
    "salary_gap_eur": "차액(EUR)",
    "salary_gap_pct": "차이율(%)",
    "salary_value_label": "연봉 가치",
    "salary_value_score": "가치 점수",
    "salary_efficiency_score": "연봉 효율",
    "overall_role_score": "종합 역할 점수",
    "result_score": "역할 적합 점수",
    "selected_role": "선택 역할",
    "similarity_score": "유사도",
    "similarity_label": "유사도 라벨",
    "similarity_reason_summary": "유사도 근거",
    "selected_sort_by": "정렬 기준",
    "selected_sort_score": "정렬 점수",
    "data_quality_note": "데이터 메모",
    "value_reason_summary": "평가 근거",
}

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

SIMILARITY_FOCUS_LABELS = {
    "overall": "전체 스타일 유사",
    "role": "역할 적합도 유사",
    "attack": "공격 성향 유사",
    "passing": "창의성/전개 성향 유사",
    "defense": "수비 성향 유사",
    "physical": "압박/활동량 유사",
    "value": "연봉 가치까지 고려",
}

POSITION_SCOPE_LABELS = {
    "same_position": "같은 포지션 그룹만",
    "adjacent_position": "인접 포지션까지",
    "all": "전체 포지션",
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


# ---- 공통 보조 함수 -------------------------------------------------------


def _html(markup: str) -> None:
    cleaned = dedent(markup).strip()

    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


def _num(value, default: float = 0.0) -> float:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return default
    return float(number)


def _safe_text(value, default: str = "-") -> str:
    if value in [None, ""]:
        return default
    return str(value)


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


def _fmt_score(value, digits: int = 1) -> str:
    number = _num(value, 0.0)
    if digits <= 0:
        return f"{number:.0f}"
    return f"{number:.{digits}f}"


def _as_records(players: pd.DataFrame) -> list[dict]:
    if players.empty:
        return []
    return players.where(pd.notna(players), "").to_dict("records")


def _display_table(df: pd.DataFrame, columns: Iterable[str]) -> None:
    available = [column for column in columns if column in df.columns]
    display_df = df[available].copy() if available else df.copy()

    display_df = display_df.rename(
        columns={column: DISPLAY_COLUMNS.get(column, column) for column in display_df.columns}
    )

    seen: dict[str, int] = {}
    unique_columns: list[str] = []

    for column in display_df.columns:
        column_name = str(column)

        if column_name not in seen:
            seen[column_name] = 0
            unique_columns.append(column_name)
        else:
            seen[column_name] += 1
            unique_columns.append(f"{column_name}_{seen[column_name] + 1}")

    display_df.columns = unique_columns

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def _condition_summary(conditions: dict) -> None:
    search_type = conditions.get("search_type")
    chips = [
        conditions.get("intent_label", "스카우팅"),
        f"요청: {conditions.get('request', '-')}",
    ]

    if search_type == "role_based":
        chips.extend(
            [
                f"역할: {conditions.get('role_key', '-')}",
                f"포지션: {conditions.get('position_group', 'ALL')}",
                f"리그: {conditions.get('league', 'ALL')}",
            ]
        )
    elif search_type == "value":
        chips.extend(
            [
                f"선수: {conditions.get('player_label', conditions.get('player_id', '-'))}",
                "평가 방식: Azure 우선 · 로컬 ONNX/PKL 대체",
                "설명: SHAP 기반 주요 영향 요인 표시",
            ]
        )
    elif search_type == "similar":
        chips.extend(
            [
                f"기준 선수: {conditions.get('base_player_label', conditions.get('base_player_id', '-'))}",
                f"유사도: {SIMILARITY_FOCUS_LABELS.get(conditions.get('similarity_focus'), conditions.get('similarity_focus', '-'))}",
                f"범위: {POSITION_SCOPE_LABELS.get(conditions.get('position_scope'), conditions.get('position_scope', '-'))}",
            ]
        )
    elif search_type == "advanced":
        chips.extend(
            [
                f"포지션: {conditions.get('position_group', 'ALL')}",
                f"리그: {conditions.get('league', 'ALL')}",
                f"팀: {conditions.get('team', 'ALL')}",
                f"정렬: {SORT_LABELS.get(conditions.get('sort_by'), conditions.get('sort_by', 'overall_role_score'))}",
            ]
        )

    chip_html = "".join(
        f"<span class='condition-chip'>{html.escape(str(chip))}</span>"
        for chip in chips
        if chip
    )

    _html(
        f"""
        <div class="scout-result-condition-panel">
          <div class="scout-result-section-kicker">SEARCH CONDITIONS</div>
          <div class="scout-result-section-title">검색 조건</div>
          <div class="scout-result-chip-row">{chip_html}</div>
        </div>
        """
    )


def _kpi_card(label: str, value: str, caption: str = "") -> str:
    return f"""
    <div class="sr-kpi-card">
      <div class="sr-kpi-label">{html.escape(label)}</div>
      <div class="sr-kpi-value">{html.escape(str(value))}</div>
      <div class="sr-kpi-caption">{html.escape(caption)}</div>
    </div>
    """


def _render_result_hero(
    *,
    kicker: str,
    title: str,
    subtitle: str,
    badge: str,
) -> None:
    _html(
        f"""
        <div class="sr-hero">
          <div>
            <div class="sr-hero-kicker">{html.escape(kicker)}</div>
            <div class="sr-hero-title">{html.escape(title)}</div>
            <div class="sr-hero-subtitle">{html.escape(subtitle)}</div>
          </div>
          <div class="sr-hero-badge">{html.escape(badge)}</div>
        </div>
        """
    )


def _render_kpi_grid(kpis: list[tuple[str, str, str]]) -> None:
    kpi_html = "".join(_kpi_card(label, value, caption) for label, value, caption in kpis)
    _html(f"<div class='sr-kpi-grid'>{kpi_html}</div>")


def _salary_status_class(label: object) -> str:
    text = str(label or "")
    if "저평가" in text:
        return "undervalued"
    if "고평가" in text:
        return "overvalued"
    if "적정" in text:
        return "fair"
    return "unknown"


def _score_width(value) -> float:
    return max(2.0, min(100.0, _num(value, 0.0)))


def _candidate_card(row: pd.Series, rank: int, mode: str) -> str:
    name = html.escape(_safe_text(row.get("player_name"), "Unknown"))
    team = html.escape(_safe_text(row.get("team")))
    league = html.escape(_safe_text(row.get("league")))
    position = html.escape(_safe_text(row.get("position_group")))
    age = html.escape(_safe_text(row.get("age")))
    salary = html.escape(_fmt_money(row.get("salary_annual_gross_eur")))
    value_label = html.escape(_safe_text(row.get("salary_value_label"), "정보 없음"))
    status_class = _salary_status_class(value_label)

    if mode == "similar":
        main_label = "유사도"
        main_score = _num(row.get("similarity_score"))
        pill = _safe_text(row.get("similarity_label"), "유사 후보")
        reason = _safe_text(row.get("similarity_reason_summary"), "유사도 근거가 제공되지 않았습니다.")
    elif mode == "advanced":
        main_label = "정렬 점수"
        main_score = _num(row.get("selected_sort_score", row.get("overall_role_score")))
        sort_by = SORT_LABELS.get(row.get("selected_sort_by"), _safe_text(row.get("selected_sort_by")))
        pill = f"{sort_by}"
        reason = _safe_text(row.get("data_quality_note"), "데이터 메모가 없습니다.")
    else:
        main_label = "역할 적합도"
        main_score = _num(row.get("result_score", row.get("overall_role_score")))
        pill = _safe_text(row.get("selected_role"), "역할 기반")
        reason = _safe_text(row.get("data_quality_note"), "데이터 메모가 없습니다.")

    width = _score_width(main_score)
    overall = _num(row.get("overall_role_score"))
    value_score = _num(row.get("salary_value_score"))

    return f"""
    <div class="sr-candidate-card">
      <div class="sr-rank">#{rank}</div>
      <div class="sr-candidate-main">
        <div class="sr-candidate-top">
          <div>
            <div class="sr-candidate-name">{name}</div>
            <div class="sr-candidate-meta">{team} · {league} · {position} · {age}세</div>
          </div>
          <div class="sr-card-pill">{html.escape(str(pill))}</div>
        </div>

        <div class="sr-score-line">
          <div class="sr-score-head">
            <span>{html.escape(main_label)}</span>
            <b>{main_score:.1f}</b>
          </div>
          <div class="sr-score-track">
            <div class="sr-score-fill" style="width:{width:.1f}%"></div>
          </div>
        </div>

        <div class="sr-mini-grid">
          <div><span>종합 역할</span><b>{overall:.1f}</b></div>
          <div><span>연봉 가치</span><b>{value_score:.1f}</b></div>
          <div><span>연봉</span><b>{salary}</b></div>
          <div><span>가치 판단</span><b class="{status_class}">{value_label}</b></div>
        </div>

        <div class="sr-card-note">{html.escape(reason)}</div>
      </div>
    </div>
    """


def _render_candidate_showcase(df: pd.DataFrame, mode: str, title: str) -> None:
    top_df = df.head(3).copy()

    cards_html = "".join(
        _candidate_card(row, index + 1, mode)
        for index, (_, row) in enumerate(top_df.iterrows())
    )

    _html(
        f"""
        <div class="sr-section">
          <div class="sr-section-head">
            <div>
              <div class="scout-result-section-kicker">TOP CANDIDATES</div>
              <div class="scout-result-section-title">{html.escape(title)}</div>
            </div>
            <div class="sr-section-badge">Top {len(top_df)}</div>
          </div>
          <div class="sr-candidate-grid">
            {cards_html}
          </div>
        </div>
        """
    )


def _bar_item(label: str, value: int, total: int) -> str:
    width = 0 if total <= 0 else max(5, value / total * 100)

    return f"""
    <div class="sr-breakdown-row">
      <div class="sr-breakdown-label">{html.escape(label)}</div>
      <div class="sr-breakdown-track">
        <div class="sr-breakdown-fill" style="width:{width:.1f}%"></div>
      </div>
      <div class="sr-breakdown-value">{value}</div>
    </div>
    """


def _render_breakdown_panel(df: pd.DataFrame) -> None:
    left = ""
    right = ""

    if "league" in df.columns:
        counts = df["league"].fillna("-").astype(str).value_counts().head(5)
        left = "".join(_bar_item(label, int(value), len(df)) for label, value in counts.items())

    if "position_group" in df.columns:
        counts = df["position_group"].fillna("-").astype(str).value_counts().head(5)
        right = "".join(_bar_item(label, int(value), len(df)) for label, value in counts.items())

    _html(
        f"""
        <div class="sr-breakdown-grid">
          <div class="sr-breakdown-card">
            <div class="sr-breakdown-title">리그 분포</div>
            {left or "<div class='sr-empty-text'>리그 데이터가 없습니다.</div>"}
          </div>
          <div class="sr-breakdown-card">
            <div class="sr-breakdown-title">포지션 분포</div>
            {right or "<div class='sr-empty-text'>포지션 데이터가 없습니다.</div>"}
          </div>
        </div>
        """
    )


def _render_selected_detail(df: pd.DataFrame, mode: str, key: str) -> None:
    labels = [
        f"{index + 1}. {row.get('player_name', 'Unknown')} · {row.get('team', '-')}"
        for index, (_, row) in enumerate(df.iterrows())
    ]

    selected_label = st.selectbox(
        "상세 분석할 후보 선택",
        labels,
        index=0,
        key=key,
    )

    selected_index = labels.index(selected_label)
    row = df.iloc[selected_index]

    name = html.escape(_safe_text(row.get("player_name"), "Unknown"))
    team = html.escape(_safe_text(row.get("team")))
    league = html.escape(_safe_text(row.get("league")))
    position = html.escape(_safe_text(row.get("position_group")))
    salary = html.escape(_fmt_money(row.get("salary_annual_gross_eur")))
    value_label = html.escape(_safe_text(row.get("salary_value_label"), "정보 없음"))

    if mode == "similar":
        headline = f"{_fmt_score(row.get('similarity_score'))} 유사도"
        summary = _safe_text(row.get("similarity_reason_summary"), "유사도 근거가 제공되지 않았습니다.")
        score_a_label, score_a_value = "유사도", row.get("similarity_score")
    elif mode == "advanced":
        sort_label = SORT_LABELS.get(row.get("selected_sort_by"), _safe_text(row.get("selected_sort_by")))
        headline = f"{sort_label} 기준 상위 후보"
        summary = _safe_text(row.get("data_quality_note"), "데이터 메모가 없습니다.")
        score_a_label, score_a_value = sort_label, row.get("selected_sort_score")
    else:
        headline = f"{_safe_text(row.get('selected_role'), '역할')} 적합 후보"
        summary = _safe_text(row.get("data_quality_note"), "데이터 메모가 없습니다.")
        score_a_label, score_a_value = "역할 적합도", row.get("result_score")

    score_rows = [
        ("종합 역할 점수", row.get("overall_role_score")),
        ("연봉 가치 점수", row.get("salary_value_score")),
        ("연봉 효율 점수", row.get("salary_efficiency_score")),
    ]

    score_html = "".join(
        f"""
        <div class="sr-detail-score">
          <span>{html.escape(str(label))}</span>
          <b>{_fmt_score(value)}</b>
          <div class="sr-score-track"><div class="sr-score-fill" style="width:{_score_width(value):.1f}%"></div></div>
        </div>
        """
        for label, value in [(score_a_label, score_a_value), *score_rows]
        if value not in [None, ""]
    )

    _html(
        f"""
        <div class="sr-detail-card">
          <div class="sr-detail-top">
            <div>
              <div class="sr-detail-kicker">SELECTED CANDIDATE</div>
              <div class="sr-detail-name">{name}</div>
              <div class="sr-detail-meta">{team} · {league} · {position} · 연봉 {salary}</div>
            </div>
            <div class="sr-detail-badge">{html.escape(headline)}</div>
          </div>

          <div class="sr-detail-grid">
            <div class="sr-detail-summary">
              <div class="sr-detail-title">후보 해석</div>
              <p>{html.escape(summary)}</p>
              <div class="sr-detail-value">연봉 가치 판단 <b>{value_label}</b></div>
            </div>
            <div class="sr-detail-scores">
              {score_html}
            </div>
          </div>
        </div>
        """
    )


def _render_raw_table(df: pd.DataFrame, columns: list[str], label: str = "원본 후보 테이블 보기") -> None:
    """개발 모드에서만 가공 전 후보 테이블을 표시합니다."""
    if not is_development_mode():
        return

    with st.expander(label, expanded=False):
        _display_table(df, columns)


def _friendly_warning(warning: object) -> str | None:
    """내부 데이터 경고를 사용자가 이해할 수 있는 안내로 바꿉니다."""
    text = str(warning or "").strip()
    lowered = text.lower()

    if not text:
        return None
    if "low_minutes" in lowered or "low_sample" in lowered:
        return "출전 기록이 적어 예측의 불확실성이 클 수 있습니다."
    if "passing_proxy_limited" in lowered:
        return "일부 패스 기록이 제한되어 대체 지표를 사용했습니다."
    if "missing" in lowered or "imputed" in lowered:
        return "일부 기록이 없어 보정값을 사용했습니다."
    return None


# ---- 검색 유형별 결과 화면 ------------------------------------------------


def _render_role_based_result(players: pd.DataFrame, conditions: dict) -> None:
    rows = find_role_based_players(conditions, players=_as_records(players))

    if not rows:
        st.warning("조건에 맞는 역할 기반 후보를 찾지 못했습니다. 나이, 연봉, 출전 시간 조건을 완화해 주세요.")
        return

    df = pd.DataFrame(rows).head(int(conditions.get("top_n") or 20)).reset_index(drop=True)
    top = df.iloc[0]

    _render_result_hero(
        kicker="ROLE FIT DASHBOARD",
        title=f"{conditions.get('role_key', '-')} 역할 후보 분석",
        subtitle="백엔드가 계산한 역할 적합도, 우선 지표 보정 점수, 연봉 가치 정보를 함께 보여줍니다.",
        badge=f"{len(df)}명 후보",
    )

    _render_kpi_grid(
        [
            ("최고 역할 적합도", _fmt_score(top.get("result_score")), "선택 역할 기준"),
            ("평균 역할 적합도", _fmt_score(df["result_score"].mean()), "결과 후보 평균"),
            ("저평가 후보", f"{df['salary_value_label'].astype(str).str.contains('저평가', na=False).sum()}명", "연봉 가치 라벨 기준"),
            ("평균 연봉", _fmt_money(df["salary_annual_gross_eur"].mean()), "검색 결과 평균"),
        ]
    )

    _render_candidate_showcase(df, "role", "역할 기반 추천 상위 후보")
    _render_breakdown_panel(df)
    _render_selected_detail(df, "role", "role_result_selected_candidate")

    _render_raw_table(
        df,
        [
            "player_name",
            "team",
            "league",
            "position_group",
            "age",
            "minutes",
            "selected_role",
            "result_score",
            "overall_role_score",
            "salary_value_label",
            "salary_value_score",
            "salary_efficiency_score",
            "salary_annual_gross_eur",
            "data_quality_note",
        ],
    )


def _render_value_result(players: pd.DataFrame, conditions: dict) -> None:
    player_id = str(conditions.get("player_id") or "")
    player_label = str(conditions.get("player_label") or player_id)

    if not player_id:
        st.error("평가할 선수가 선택되지 않았습니다. 검색 페이지에서 다시 선택해 주세요.")
        return

    try:
        result = evaluate_player_value(
            player_id=player_id,
            include_shap=True,
            top_features=8,
        )
    except Exception as exc:
        st.error("선수 가치 평가를 실행하지 못했습니다.")
        st.caption("분석 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
        if is_development_mode():
            with st.expander("개발자 정보 · 상세 오류", expanded=False):
                st.exception(exc)
        return

    render_salary_value_dashboard(result, player_label=player_label)

    warnings = result.get("warnings", []) or []

    friendly_warnings = {
        message
        for warning in warnings
        if (message := _friendly_warning(warning))
    }

    if friendly_warnings:
        with st.expander("데이터 주의사항", expanded=False):
            for warning in sorted(friendly_warnings):
                st.caption(f"- {warning}")

    if is_development_mode():
        with st.expander("개발자 정보 · 선수 가치 평가 원본 응답", expanded=False):
            st.json(result)


def _render_similar_result(players: pd.DataFrame, conditions: dict) -> None:
    base_player_id = str(conditions.get("base_player_id") or "")

    if not base_player_id:
        st.error("기준 선수가 선택되지 않았습니다. 검색 페이지에서 다시 선택해 주세요.")
        return

    filters = {
        "base_player_id": base_player_id,
        "similarity_focus": conditions.get("similarity_focus") or "overall",
        "position_scope": conditions.get("position_scope") or "same_position",
        "league": conditions.get("league") or "ALL",
        "age_max": conditions.get("age_max"),
        "max_salary": conditions.get("max_salary"),
        "min_minutes": conditions.get("min_minutes") or 700,
        "top_n": conditions.get("top_n") or 20,
    }

    try:
        rows = find_similar_players(filters, players=_as_records(players))
    except Exception as exc:
        st.error("유사 선수 탐색을 실행하지 못했습니다.")
        st.caption(f"기준 선수 ID, 데이터셋, 필터 조건을 확인해 주세요. 상세 오류: {exc}")
        return

    if not rows:
        st.warning("조건에 맞는 유사 후보가 없습니다. 나이, 연봉, 출전 시간, 포지션 범위를 완화해 주세요.")
        return

    df = pd.DataFrame(rows).reset_index(drop=True)
    top = df.iloc[0]
    base_name = str(top.get("base_player_name", conditions.get("base_player_label", "기준 선수")))
    focus = str(filters["similarity_focus"])
    scope = str(filters["position_scope"])

    _render_result_hero(
        kicker="SIMILARITY DASHBOARD",
        title=f"{base_name} 대체 후보 분석",
        subtitle="백엔드 유사도 계산 결과와 연봉 가치, 유사도 근거를 함께 비교합니다.",
        badge=f"{len(df)}명 후보",
    )

    _render_kpi_grid(
        [
            ("최고 유사도", _fmt_score(top.get("similarity_score")), "기준 선수 대비"),
            ("유사도 기준", SIMILARITY_FOCUS_LABELS.get(focus, focus), "탐색 방식"),
            ("포지션 범위", POSITION_SCOPE_LABELS.get(scope, scope), "탐색 범위"),
            ("평균 연봉", _fmt_money(df["salary_annual_gross_eur"].mean()), "후보 평균"),
        ]
    )

    _render_candidate_showcase(df, "similar", "대체 후보 상위 리스트")
    _render_breakdown_panel(df)
    _render_selected_detail(df, "similar", "similar_result_selected_candidate")

    _render_raw_table(
        df,
        [
            "player_name",
            "team",
            "league",
            "position_group",
            "age",
            "minutes",
            "salary_annual_gross_eur",
            "similarity_score",
            "similarity_label",
            "salary_value_label",
            "salary_value_score",
            "similarity_reason_summary",
            "data_quality_note",
        ],
    )


def _render_advanced_result(players: pd.DataFrame, conditions: dict) -> None:
    rows = advanced_search_players(conditions, players=_as_records(players))

    if not rows:
        st.warning("세밀 조건에 맞는 후보가 없습니다. 필터를 완화해 주세요.")
        return

    df = pd.DataFrame(rows).reset_index(drop=True)
    top = df.iloc[0]

    sort_by = str(conditions.get("sort_by", "overall_role_score"))
    sort_label = SORT_LABELS.get(sort_by, sort_by)
    direction_label = "높은 순" if conditions.get("sort_direction") != "asc" else "낮은 순"

    _render_result_hero(
        kicker="ADVANCED FILTER DASHBOARD",
        title="세밀 조건 검색 결과",
        subtitle="포지션, 리그, 연봉, 출전 시간, 점수 필터를 통과한 후보를 정렬 기준별로 보여줍니다.",
        badge=f"{len(df)}명 후보",
    )

    _render_kpi_grid(
        [
            ("결과 수", f"{len(df)}명", "필터 통과 후보"),
            ("정렬 기준", sort_label, direction_label),
            ("최고 정렬 점수", _fmt_score(top.get("selected_sort_score")), "상위 후보 기준"),
            ("평균 연봉", _fmt_money(df["salary_annual_gross_eur"].mean()), "검색 결과 평균"),
        ]
    )

    _render_candidate_showcase(df, "advanced", "세밀 조건 검색 상위 후보")
    _render_breakdown_panel(df)
    _render_selected_detail(df, "advanced", "advanced_result_selected_candidate")

    _render_raw_table(
        df,
        [
            "player_name",
            "team",
            "league",
            "position_group",
            "age",
            "minutes",
            "salary_annual_gross_eur",
            "overall_role_score",
            "salary_value_label",
            "salary_value_score",
            "salary_efficiency_score",
            "selected_sort_by",
            "selected_sort_score",
            "data_quality_note",
        ],
    )

    if is_development_mode():
        with st.expander("개발자 정보 · 검색 조건 원본", expanded=False):
            st.json(conditions)


# ---- 화면 진입점 ----------------------------------------------------------


def render() -> None:
    st.session_state.current_page = "scout_result"
    st.session_state.user_mode = "scout"

    players = load_scout_players()
    conditions = get_scout_conditions()
    search_type = str(conditions.get("search_type") or "role_based")

    page_title("스카우팅 결과", f"{conditions.get('intent_label', '스카우팅')} 결과")

    if st.button("← 처음 검색으로 돌아가기"):
        move_page("scout_search")
        st.rerun()

    st.divider()

    _condition_summary(conditions)

    if players.empty:
        st.error("스카우터 선수 데이터가 비어 있습니다. data/processed/scout_player_view_2526.csv를 확인해 주세요.")
        return

    # 페이지 이동 직후의 기본 실행 화면 대신 사용자에게 이해하기 쉬운 안내를 표시합니다.
    with st.spinner("선수 데이터를 분석하고 있어요. 잠시만 기다려 주세요."):
        if search_type == "value":
            _render_value_result(players, conditions)
        elif search_type == "similar":
            _render_similar_result(players, conditions)
        elif search_type == "advanced":
            _render_advanced_result(players, conditions)
        else:
            _render_role_based_result(players, conditions)
