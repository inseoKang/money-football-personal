import pandas as pd

from src.coach.config import COLUMN_MAP, PLAYERS_FILE
from src.coach.formation import get_formation_positions
from src.coach.scoring import calculate_player_score
from src.coach.validators import validate_player_columns

def load_players():
    players = pd.read_csv(PLAYERS_FILE)
    validate_player_columns(players)
    return players

def recommend_lineup(formation_name, tactic="balanced"):
    players = load_players()
    required_positions = get_formation_positions(formation_name)

    lineup = []
    used_player_ids = set()
    missing_positions = []

    for position in required_positions:
        position_column = COLUMN_MAP["position"]
        player_id_column = COLUMN_MAP["player_id"]

        candidates = players[
            (players[position_column] == position)
            & (~players[player_id_column].isin(used_player_ids))
        ].copy()

        if candidates.empty:
            missing_positions.append(position)
            lineup.append({
                "position": position,
                "player": None,
                "score": None,
                "reason": f"{position} 포지션에 선택 가능한 선수가 없습니다.",
            })
            continue

        candidates["coach_score"] = candidates.apply(
            lambda player: calculate_player_score(player, tactic),
            axis=1,
        )

        best_player = candidates.sort_values(
            "coach_score",
            ascending=False,
        ).iloc[0]

        used_player_ids.add(best_player[player_id_column])

        lineup.append({
            "position": position,
            "player": {
                "player_id": int(best_player[COLUMN_MAP["player_id"]]),
                "name": best_player[COLUMN_MAP["name"]],
                "original_position": best_player[COLUMN_MAP["position"]],
            },
            "score": float(best_player["coach_score"]),
            "reason": f"{position} 포지션에서 {tactic} 전술 기준 점수가 가장 높습니다.",
        })

    return {
        "formation": formation_name,
        "tactic": tactic,
        "lineup": lineup,
        "missing_positions": missing_positions,
    }