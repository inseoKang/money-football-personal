from __future__ import annotations

import pandas as pd


POSITION_ORDER = ["GK", "DF", "MF", "FW"]


def build_dashboard_payload(players_df) -> dict:
    players = players_df.copy()
    return {
        "summary": _summary(players),
        "positionDistribution": _position_distribution(players),
        "leagueSummary": _league_summary(players),
        "clubSummary": _club_summary(players),
        "topPlayers": {
            "overall": _top_players(players, "overall_score", 8),
            "attack": _top_players(players, "attack_score", 8),
            "defense": _top_players(players, "defense_score", 8),
            "keeper": _top_players(players[players["position_group"].eq("GK")], "keeper_score", 8),
            "goals": _top_players(players, "goals", 8),
            "assists": _top_players(players, "assists", 8),
        },
        "positionScores": _position_scores(players),
    }


def _summary(players) -> dict:
    return {
        "players": int(len(players)),
        "leagues": int(players["league"].nunique()),
        "clubs": int(players["club"].nunique()),
        "avgAge": round(float(players["age"].mean()), 2),
        "totalGoals": int(players["goals"].sum()),
        "totalAssists": int(players["assists"].sum()),
        "avgOverall": round(float(players["overall_score"].mean()), 2),
        "avgMinutes": round(float(players["minutes"].mean()), 2),
    }


def _position_distribution(players) -> list[dict]:
    counts = players["position_group"].value_counts().reindex(POSITION_ORDER).fillna(0)
    return [
        {"position": position, "players": int(counts[position])}
        for position in POSITION_ORDER
    ]


def _league_summary(players) -> list[dict]:
    grouped = (
        players.groupby("league", as_index=False)
        .agg(
            players=("player", "count"),
            clubs=("club", "nunique"),
            avgOverall=("overall_score", "mean"),
            goals=("goals", "sum"),
            assists=("assists", "sum"),
            avgAge=("age", "mean"),
        )
        .sort_values("avgOverall", ascending=False)
    )
    return _round_records(grouped)


def _club_summary(players, limit: int = 12) -> list[dict]:
    grouped = (
        players.groupby(["league", "club"], as_index=False)
        .agg(
            players=("player", "count"),
            avgOverall=("overall_score", "mean"),
            goals=("goals", "sum"),
            assists=("assists", "sum"),
            avgAge=("age", "mean"),
        )
        .sort_values("avgOverall", ascending=False)
        .head(limit)
    )
    return _round_records(grouped)


def _position_scores(players) -> list[dict]:
    grouped = (
        players.groupby("position_group", as_index=False)
        .agg(
            players=("player", "count"),
            overall=("overall_score", "mean"),
            attack=("attack_score", "mean"),
            defense=("defense_score", "mean"),
            keeper=("keeper_score", "mean"),
            stamina=("stamina_score", "mean"),
            discipline=("discipline_score", "mean"),
        )
    )
    order = {position: index for index, position in enumerate(POSITION_ORDER)}
    grouped["order"] = grouped["position_group"].map(order).fillna(99)
    grouped = grouped.sort_values("order").drop(columns=["order"])
    return _round_records(grouped)


def _top_players(players, score_column: str, limit: int) -> list[dict]:
    if players.empty:
        return []

    view = players.sort_values(score_column, ascending=False).head(limit)
    rows = []
    for _, player in view.iterrows():
        rows.append(
            {
                "salaryId": int(player["salary_id"]),
                "player": player["player"],
                "club": player["club"],
                "league": player["league"],
                "position": player["position_group"],
                "value": round(float(player[score_column]), 2),
                "overall": round(float(player["overall_score"]), 2),
            }
        )
    return rows


def _round_records(df: pd.DataFrame) -> list[dict]:
    records = df.to_dict(orient="records")
    for record in records:
        for key, value in list(record.items()):
            if isinstance(value, float):
                record[key] = round(value, 2)
            elif hasattr(value, "item"):
                record[key] = value.item()
    return records
