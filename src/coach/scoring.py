from src.coach.config import COLUMN_MAP, TACTIC_WEIGHTS


def calculate_player_score(player, tactic="balanced"):
    if tactic not in TACTIC_WEIGHTS:
        raise ValueError(f"지원하지 않는 전술입니다: {tactic}")

    weights = TACTIC_WEIGHTS[tactic]
    total_score = 0

    for stat_name, weight in weights.items():
        column_name = COLUMN_MAP[stat_name]
        total_score += float(player[column_name]) * weight

    return round(total_score, 2)