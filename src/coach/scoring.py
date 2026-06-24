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


def normalize_position(value: str) -> str:
    if value is None:
        return ""

    return str(value).strip().upper()


POSITION_COMPATIBILITY = {
    "GK": ["GK"],

    "CB": ["CB", "LCB", "RCB", "DF", "DEF"],
    "LB": ["LB", "LWB", "CB", "DF", "DEF"],
    "RB": ["RB", "RWB", "CB", "DF", "DEF"],

    "DM": ["DM", "CDM", "CM", "MF", "MID"],
    "CM": ["CM", "DM", "CDM", "AM", "CAM", "MF", "MID"],
    "AM": ["AM", "CAM", "CM", "FW", "MID"],

    "LW": ["LW", "LM", "RW", "RM", "ST", "CF", "FW", "FWD"],
    "RW": ["RW", "RM", "RWF", "LW", "LM", "ST", "CF", "FW", "FWD"],
    "ST": ["ST", "CF", "FW", "FWD", "LW", "RW"],
}


def is_position_compatible(player: dict, role: str) -> bool:
    target_role = normalize_position(role)

    position_values = [
        player.get("position"),
        player.get("detail_position"),
        player.get("position_group"),
        player.get("role"),
    ]

    compatible_positions = POSITION_COMPATIBILITY.get(target_role, [target_role])

    for value in position_values:
        normalized = normalize_position(value)

        if not normalized:
            continue

        if normalized in compatible_positions:
            return True

        # "RW,LW", "RW / ST", "LW;RW" 같은 문자열 대응
        for compatible_position in compatible_positions:
            if compatible_position in normalized:
                return True

    return False


def role_score(player, role):
    role = normalize_position(role)

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

    # 핵심 추가 부분:
    # 포지션이 정확히 맞거나 호환되면 점수 유지,
    # 안 맞아도 RW/LW/ST 같은 공격 슬롯은 완전히 제외하지 않고 약간만 감점.
    if is_position_compatible(player, role):
        position_multiplier = 1.0
    elif role in ["RW", "LW", "ST"]:
        position_multiplier = 0.88
    else:
        position_multiplier = 0.75

    total_score *= position_multiplier

    return round(max(0, min(100, total_score)), 2)
