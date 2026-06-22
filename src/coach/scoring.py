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
        raise ValueError(f"지원하지 않는 전술입니다: {tactic}")

    weights = TACTIC_WEIGHTS[tactic]
    total_score = 0

    for stat_name, weight in weights.items():
        column_name = COLUMN_MAP[stat_name]
        total_score += safe_number(player, column_name) * weight

    return round(total_score, 2)


def role_score(player, role):
    role_weights = {
        "GK": {
            "gk_score": 0.7,
            "defense_score": 0.1,
            "physical_score": 0.1,
            "stability_score": 0.1,
        },
        "CB": {
            "defense_score": 0.45,
            "physical_score": 0.25,
            "stability_score": 0.15,
            "midfield_score": 0.1,
            "pace_score": 0.05,
        },
        "LB": {
            "defense_score": 0.3,
            "pace_score": 0.25,
            "stamina_score": 0.2,
            "midfield_score": 0.15,
            "attack_score": 0.1,
        },
        "RB": {
            "defense_score": 0.3,
            "pace_score": 0.25,
            "stamina_score": 0.2,
            "midfield_score": 0.15,
            "attack_score": 0.1,
        },
        "DM": {
            "defense_score": 0.3,
            "midfield_score": 0.3,
            "stamina_score": 0.15,
            "physical_score": 0.15,
            "stability_score": 0.1,
        },
        "CM": {
            "midfield_score": 0.4,
            "stamina_score": 0.2,
            "defense_score": 0.15,
            "attack_score": 0.15,
            "stability_score": 0.1,
        },
        "AM": {
            "attack_score": 0.3,
            "midfield_score": 0.3,
            "pace_score": 0.15,
            "stamina_score": 0.1,
            "stability_score": 0.15,
        },
        "LW": {
            "attack_score": 0.35,
            "pace_score": 0.25,
            "midfield_score": 0.15,
            "stamina_score": 0.15,
            "physical_score": 0.1,
        },
        "RW": {
            "attack_score": 0.35,
            "pace_score": 0.25,
            "midfield_score": 0.15,
            "stamina_score": 0.15,
            "physical_score": 0.1,
        },
        "ST": {
            "attack_score": 0.45,
            "physical_score": 0.2,
            "pace_score": 0.15,
            "stamina_score": 0.1,
            "stability_score": 0.1,
        },
    }

    weights = role_weights.get(role, role_weights["CM"])

    total_score = 0
    for score_name, weight in weights.items():
        total_score += safe_number(player, score_name) * weight

    if total_score == 0:
        total_score = calculate_player_score(player, "balanced")

    return round(max(0, min(100, total_score)), 2)