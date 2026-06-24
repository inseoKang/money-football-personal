from __future__ import annotations

import pandas as pd


def get_dashboard_summary(players: pd.DataFrame) -> dict:
    if players.empty:
        return {
            "player_count": 0,
            "avg_overall": 0,
            "avg_market_value": 0,
            "top_player": "-",
        }

    top_row = players.sort_values("overall", ascending=False).head(1).iloc[0]

    return {
        "player_count": len(players),
        "avg_overall": int(round(players["overall"].mean())),
        "avg_market_value": int(round(players["market_value"].mean())) if "market_value" in players.columns else 0,
        "top_player": top_row["name"],
    }


def sort_players(players: pd.DataFrame, sort_key: str) -> pd.DataFrame:
    if players.empty:
        return players

    sort_map = {
        "종합 점수 높은 순": ("overall", False),
        "시장가치 높은 순": ("market_value", False),
        "공격 점수 높은 순": ("attack_score", False),
        "수비 점수 높은 순": ("defense_score", False),
        "나이 어린 순": ("age", True),
    }

    column, ascending = sort_map.get(sort_key, ("overall", False))

    if column not in players.columns:
        return players

    return players.sort_values(column, ascending=ascending).reset_index(drop=True)


def get_position_distribution(players: pd.DataFrame) -> pd.DataFrame:
    if players.empty or "position" not in players.columns:
        return pd.DataFrame(columns=["position", "count"])

    return (
        players["position"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "position", "position": "count"})
    )