from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.constants import NUMERIC_COLUMNS, PLAYERS_CSV_PATH, SCOUT_PLAYERS_CSV_PATH


def _normalize_barcelona_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Barcelona CSV 컬럼을 앱 내부에서 쓰는 공통 컬럼명으로 변환합니다.

    원본 CSV 예시:
    Player, Squad, Nation, Pos, Age, MP, Starts, Min, Gls, Ast, G+A, image_path

    앱 내부 기대 컬럼:
    name, position, detail_position, club, nation, age, overall, image_path ...
    """

    rename_map = {
        "Player": "name",
        "Squad": "club",
        "Nation": "nation",
        "Pos": "position",
        "Age": "age",
        "Number": "number",
        "MP": "matches",
        "Starts": "starts",
        "Min": "minutes",
        "Gls": "goals",
        "Ast": "assists",
        "G+A": "goal_assist",
        "CrdY": "yellow_cards",
        "CrdR": "red_cards",
        "Gls/90": "goals_per90",
        "Ast/90": "assists_per90",
        "G+A/90": "goal_assist_per90",
    }

    df = df.rename(columns=rename_map)

    # 기존 앱에서 detail_position을 사용하므로 없으면 position과 동일하게 채움
    if "detail_position" not in df.columns:
        df["detail_position"] = df.get("position", "")

    # 기존 앱에서 comment를 사용하므로 없으면 간단 설명 생성
    if "comment" not in df.columns:
        df["comment"] = ""

    # 기존 앱에서 score 계열 컬럼을 사용할 수 있으므로 임시 점수 생성
    # 실제 모델 점수가 들어오기 전까지 UI용으로 안정적으로 쓰기 위한 값
    numeric_base_cols = [
        "matches",
        "starts",
        "minutes",
        "goals",
        "assists",
        "goal_assist",
        "goals_per90",
        "assists_per90",
        "goal_assist_per90",
    ]

    for col in numeric_base_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 포지션별 임시 점수
    if "attack_score" not in df.columns:
        df["attack_score"] = (
            df.get("goals", 0) * 6
            + df.get("assists", 0) * 4
            + df.get("goal_assist_per90", 0) * 10
        ).round(1)

    if "midfield_score" not in df.columns:
        df["midfield_score"] = (
            df.get("assists", 0) * 5
            + df.get("starts", 0) * 1.5
            + df.get("minutes", 0) / 120
        ).round(1)

    if "defense_score" not in df.columns:
        df["defense_score"] = (
            df.get("starts", 0) * 1.5
            + df.get("minutes", 0) / 100
        ).round(1)

    if "pace_score" not in df.columns:
        df["pace_score"] = 70

    if "physical_score" not in df.columns:
        df["physical_score"] = 70

    if "stamina_score" not in df.columns:
        df["stamina_score"] = (
            60 + df.get("minutes", 0) / 100
        ).clip(0, 99).round(1)

    if "gk_score" not in df.columns:
        df["gk_score"] = 0.0

    # GK는 공격/미드필드 점수보다 출전시간 기반으로 임시 GK 점수 부여
    if "position" in df.columns and "minutes" in df.columns:
        gk_mask = df["position"].astype(str).str.contains("GK", na=False)

        df.loc[gk_mask, "gk_score"] = (
            60 + df.loc[gk_mask, "minutes"].astype(float) / 100
        ).clip(0, 99).round(1)

    return df


@st.cache_data(show_spinner=False)
def load_players(path: str | Path = PLAYERS_CSV_PATH) -> pd.DataFrame:
    path = Path(path)

    if not path.exists():
        st.error(f"선수 데이터 파일을 찾을 수 없습니다: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Barcelona CSV처럼 Player, Squad, Pos 컬럼이 있는 경우 앱 공통 컬럼으로 변환
    if "Player" in df.columns:
        df = _normalize_barcelona_columns(df)

    # 숫자 컬럼 변환
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 추가 숫자 컬럼도 안전하게 변환
    extra_numeric_columns = [
        "number",
        "age",
        "matches",
        "starts",
        "minutes",
        "goals",
        "assists",
        "goal_assist",
        "yellow_cards",
        "red_cards",
        "goals_per90",
        "assists_per90",
        "goal_assist_per90",
        "attack_score",
        "midfield_score",
        "defense_score",
        "pace_score",
        "physical_score",
        "stamina_score",
        "gk_score",
    ]

    for col in extra_numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "number" not in df.columns:
        df["number"] = 0

    df["number"] = pd.to_numeric(df["number"], errors="coerce").fillna(0).astype(int)

    required_text_columns = [
        "name",
        "position",
        "detail_position",
        "club",
        "nation",
        "comment",
        "image_path",
    ]

    for col in required_text_columns:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    if "overall" not in df.columns:
        score_cols = [
            col
            for col in [
                "attack_score",
                "midfield_score",
                "defense_score",
                "pace_score",
                "physical_score",
                "stamina_score",
                "gk_score",
            ]
            if col in df.columns
        ]

        if score_cols:
            df["overall"] = df[score_cols].mean(axis=1).round().astype(int)
        else:
            df["overall"] = 0

    # 앱 표시용 컬럼
    df["display_name"] = df["name"]

    df["position_label"] = df["position"].astype(str)
    detail = df["detail_position"].astype(str)

    df.loc[detail.ne("") & detail.ne(df["position_label"]), "position_label"] = (
        df["position_label"] + " · " + detail
    )

    return df


@st.cache_data(show_spinner=False)
def load_scout_players(path: str | Path = SCOUT_PLAYERS_CSV_PATH) -> pd.DataFrame:
    path = Path(path)

    if not path.exists():
        st.error(f"스카우터 데이터 파일을 찾을 수 없습니다: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)

    numeric_columns = [
        "age",
        "matches_played",
        "starts",
        "minutes",
        "nineties",
        "salary_annual_gross_eur",
        "current_salary_annual_gross_eur",
        "predicted_next_salary_annual_gross_eur",
        "salary_gap_eur",
        "salary_gap_pct",
        "salary_value_score",
        "salary_efficiency_score",
        "overall_role_score",
        "attack_score",
        "shooting_score",
        "chance_creation_score",
        "progressive_pass_score",
        "creative_pass_score",
        "pressing_score",
        "defensive_action_score",
        "ball_winning_score",
        "build_up_score",
        "aerial_defense_score",
        "goalkeeper_score",
        "role_fit_finisher",
        "role_fit_pressing_forward",
        "role_fit_creative_midfielder",
        "role_fit_progressive_passer",
        "role_fit_ball_winning_midfielder",
        "role_fit_ball_playing_defender",
        "role_fit_defensive_stopper",
        "role_fit_shot_stopper",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def filter_players(
    df: pd.DataFrame,
    keyword: str = "",
    group: str = "전체",
    nation: str = "전체",
) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.copy()

    if keyword:
        keyword = keyword.lower().strip()
        result = result[
            result["name"].str.lower().str.contains(keyword, na=False)
            | result["club"].str.lower().str.contains(keyword, na=False)
            | result["nation"].str.lower().str.contains(keyword, na=False)
        ]

    if group and group != "전체":
        if group == "DF":
            allowed = ["DF", "CB", "LB", "RB"]
        elif group == "MF":
            allowed = ["MF", "CM", "DM", "AM"]
        elif group == "FW":
            allowed = ["FW", "ST", "LW", "RW"]
        else:
            allowed = [group]

        result = result[
            result["position"].isin(allowed)
            | result["detail_position"].isin(allowed)
            | result["position"].astype(str).str.contains(group, na=False)
            | result["detail_position"].astype(str).str.contains(group, na=False)
        ]

    if nation and nation != "전체" and "nation" in result.columns:
        result = result[result["nation"].eq(nation)]

    return result.reset_index(drop=True)


def get_nation_options(df: pd.DataFrame) -> list[str]:
    if df.empty or "nation" not in df.columns:
        return ["전체"]

    nations = sorted(
        [nation for nation in df["nation"].dropna().unique() if str(nation).strip()]
    )
    return ["전체"] + nations