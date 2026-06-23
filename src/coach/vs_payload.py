from __future__ import annotations

from src.coach.lineup_payload import recommend_lineup_payload


SUMMARY_KEYS = [
    "players",
    "avg_age",
    "total_minutes",
    "total_goals",
    "total_assists",
    "avg_overall",
]

METRIC_KEYS = [
    "team_score",
    "attack",
    "midfield",
    "defense",
    "keeper",
    "position_fit",
    "balance",
    "synergy",
]


def summarize_squad(players_df) -> dict:
    players = players_df.copy()
    return {
        "players": int(len(players)),
        "avg_age": round(float(players["age"].mean()), 2) if len(players) else 0,
        "total_minutes": int(players["minutes"].sum()),
        "total_goals": int(players["goals"].sum()),
        "total_assists": int(players["assists"].sum()),
        "avg_overall": round(float(players["overall_score"].mean()), 2) if len(players) else 0,
    }


def compare_squads(left_players, right_players, formation: str = "4-3-3") -> dict:
    left_summary = summarize_squad(left_players)
    right_summary = summarize_squad(right_players)
    left_lineup = recommend_lineup_payload(left_players, formation)
    right_lineup = recommend_lineup_payload(right_players, formation)

    summary_delta = {
        key: round(left_summary[key] - right_summary[key], 2)
        for key in SUMMARY_KEYS
    }
    metric_delta = {
        key: round(left_lineup["metrics"][key] - right_lineup["metrics"][key], 2)
        for key in METRIC_KEYS
    }

    return {
        "formation": formation,
        "left": {
            "summary": left_summary,
            "lineup": left_lineup,
        },
        "right": {
            "summary": right_summary,
            "lineup": right_lineup,
        },
        "delta": {
            "summary": summary_delta,
            "metrics": metric_delta,
        },
        "winner": _pick_winner(left_lineup["metrics"]["team_score"], right_lineup["metrics"]["team_score"]),
    }


def _pick_winner(left_score: float, right_score: float) -> str:
    if abs(left_score - right_score) < 0.5:
        return "draw"
    return "left" if left_score > right_score else "right"
