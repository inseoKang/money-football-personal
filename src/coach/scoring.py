from src.coach.config import COLUMN_MAP, TACTIC_WEIGHTS


def safe_number(player, key, default=0):
    value = player.get(key, default)

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_player_score(player, tactic="balanced"):
    if tactic not in TACTIC_WEIGHTS:
        raise ValueError(f"Unsupported tactic: {tactic}")

    weights = TACTIC_WEIGHTS[tactic]
    total_score = 0

    for stat_name, weight in weights.items():
        column_name = COLUMN_MAP[stat_name]
        total_score += safe_number(player, column_name) * weight

    return round(total_score, 2)


def role_score(player, role):
    role_weights = {
        "GK": {"keeper_score": 0.70, "stamina_score": 0.15, "discipline_score": 0.15},
        "CB": {"defense_score": 0.55, "stamina_score": 0.25, "discipline_score": 0.20},
        "LB": {"defense_score": 0.40, "stamina_score": 0.30, "attack_score": 0.15, "discipline_score": 0.15},
        "RB": {"defense_score": 0.40, "stamina_score": 0.30, "attack_score": 0.15, "discipline_score": 0.15},
        "DM": {"defense_score": 0.40, "stamina_score": 0.30, "discipline_score": 0.20, "attack_score": 0.10},
        "CM": {"stamina_score": 0.35, "attack_score": 0.25, "defense_score": 0.25, "discipline_score": 0.15},
        "AM": {"attack_score": 0.45, "stamina_score": 0.25, "discipline_score": 0.20, "defense_score": 0.10},
        "LW": {"attack_score": 0.55, "stamina_score": 0.25, "discipline_score": 0.15, "defense_score": 0.05},
        "RW": {"attack_score": 0.55, "stamina_score": 0.25, "discipline_score": 0.15, "defense_score": 0.05},
        "ST": {"attack_score": 0.65, "stamina_score": 0.20, "discipline_score": 0.10, "defense_score": 0.05},
    }

    weights = role_weights.get(role, role_weights["CM"])

    total_score = 0
    for score_name, weight in weights.items():
        total_score += safe_number(player, score_name) * weight

    if total_score == 0:
        total_score = calculate_player_score(player, "balanced")

    return round(max(0, min(100, total_score)), 2)
