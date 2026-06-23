from src.coach.formation_run import get_formation_slots
from src.coach.scoring import role_score, safe_number


def _get_name_column(players_df):
    if "name" in players_df.columns:
        return "name"
    if "Player" in players_df.columns:
        return "Player"
    if "player" in players_df.columns:
        return "player"
    return None


def _get_player_by_name(players_df, player_name):
    name_column = _get_name_column(players_df)

    if name_column is None:
        return None

    matched_players = players_df[players_df[name_column] == player_name]

    if matched_players.empty:
        return None

    return matched_players.iloc[0]


def _average(values):
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return 0

    return round(sum(clean_values) / len(clean_values), 2)


def _grade(score):
    if score >= 90:
        return "S"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def calculate_team_metrics(players_df, formation, lineup):
    formation_slots = get_formation_slots(formation)

    attack_scores = []
    midfield_scores = []
    defense_scores = []
    keeper_scores = []
    position_fit_scores = []
    left_scores = []
    right_scores = []

    for slot in formation_slots:
        slot_id = slot["slot_id"]
        role = slot["role"]
        line = slot["line"]
        player_name = lineup.get(slot_id)

        if not player_name:
            continue

        player = _get_player_by_name(players_df, player_name)

        if player is None:
            continue

        fit_score = role_score(player, role)
        position_fit_scores.append(fit_score)

        if line == "FW":
            attack_scores.append(fit_score)
        elif line == "MF":
            midfield_scores.append(fit_score)
        elif line == "DF":
            defense_scores.append(fit_score)
        elif line == "GK":
            keeper_scores.append(fit_score)
            defense_scores.append(fit_score)

        if slot_id.startswith("L"):
            left_scores.append(fit_score)
        elif slot_id.startswith("R"):
            right_scores.append(fit_score)

    attack = _average(attack_scores)
    midfield = _average(midfield_scores)
    defense = _average(defense_scores)
    keeper = _average(keeper_scores)
    position_fit = _average(position_fit_scores)

    if left_scores and right_scores:
        balance = 100 - abs(_average(left_scores) - _average(right_scores))
    else:
        balance = 75

    synergy = round(
        (position_fit * 0.5)
        + (balance * 0.2)
        + (midfield * 0.15)
        + (defense * 0.15),
        2,
    )

    team_score = round(
        (attack * 0.25)
        + (midfield * 0.25)
        + (defense * 0.20)
        + (keeper * 0.10)
        + (position_fit * 0.10)
        + (balance * 0.05)
        + (synergy * 0.05),
        2,
    )

    return {
        "team_score": team_score,
        "grade": _grade(team_score),
        "attack": attack,
        "midfield": midfield,
        "defense": defense,
        "keeper": keeper,
        "position_fit": position_fit,
        "balance": round(balance, 2),
        "synergy": synergy,
    }


def build_recommendation_text(metrics):
    metric_labels = {
        "attack": "attack power",
        "midfield": "midfield control",
        "defense": "defensive stability",
        "keeper": "goalkeeper stability",
        "position_fit": "position fit",
        "balance": "left-right balance",
        "synergy": "team synergy",
    }

    advice = {
        "attack": "Add or move players with stronger finishing, shooting volume, and goal contribution.",
        "midfield": "Use midfielders with strong stamina and two-way contribution to connect defense and attack.",
        "defense": "Prioritize defenders with stronger interception and tackle profiles.",
        "keeper": "Check goalkeeper form and consider a more stable keeper if clean-sheet or save numbers are weak.",
        "position_fit": "Revisit whether each player is placed in a role that matches his position group.",
        "balance": "The side balance is uneven, so reinforce the weaker side or adjust wide roles.",
        "synergy": "The lineup needs a better mix between midfield, defense, and role fit.",
    }

    target_keys = list(metric_labels.keys())
    weakest_key = min(target_keys, key=lambda key: safe_number(metrics, key, 0))
    weakest_label = metric_labels[weakest_key]

    return (
        f"The main tactical concern in this lineup is {weakest_label}. "
        f"{advice[weakest_key]}"
    )
