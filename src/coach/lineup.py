import pandas as pd

from src.coach.config import COLUMN_MAP, PLAYERS_FILE
from src.coach.formation_run import get_formation_slots
from src.coach.formations import ROLE_ALIASES
from src.coach.scoring import calculate_player_score
from src.coach.validators import validate_player_columns


def load_players():
    players = pd.read_csv(PLAYERS_FILE)
    validate_player_columns(players)
    return players


def get_candidate_positions(role):
    return ROLE_ALIASES.get(role, [role])


def recommend_lineup(formation_name, tactic="balanced"):
    players = load_players()
    formation_slots = get_formation_slots(formation_name)

    lineup = []
    used_player_ids = set()
    missing_slots = []

    position_column = COLUMN_MAP["position"]
    player_id_column = COLUMN_MAP["player_id"]

    for slot in formation_slots:
        slot_id = slot["slot_id"]
        role = slot["role"]
        candidate_positions = get_candidate_positions(role)

        candidates = players[
            (players[position_column].isin(candidate_positions))
            & (~players[player_id_column].isin(used_player_ids))
        ].copy()

        if candidates.empty:
            missing_slots.append(slot_id)
            lineup.append({
                "slot_id": slot_id,
                "role": role,
                "line": slot["line"],
                "x": slot["x"],
                "y": slot["y"],
                "player": None,
                "score": None,
                "reason": f"{slot_id}({role}) 자리에 선택 가능한 선수가 없습니다.",
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
            "slot_id": slot_id,
            "role": role,
            "line": slot["line"],
            "x": slot["x"],
            "y": slot["y"],
            "player": {
                "player_id": int(best_player[COLUMN_MAP["player_id"]]),
                "name": best_player[COLUMN_MAP["name"]],
                "original_position": best_player[COLUMN_MAP["position"]],
            },
            "score": float(best_player["coach_score"]),
            "reason": (
                f"{slot_id}({role}) 자리에서 {tactic} 전술 기준 "
                "점수가 가장 높습니다."
            ),
        })

    return {
        "formation": formation_name,
        "tactic": tactic,
        "lineup": lineup,
        "missing_positions": missing_slots,
    }