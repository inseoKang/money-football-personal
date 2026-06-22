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
            defense_scores.append(fit_score)

        if slot_id.startswith("L"):
            left_scores.append(fit_score)
        elif slot_id.startswith("R"):
            right_scores.append(fit_score)

    attack = _average(attack_scores)
    midfield = _average(midfield_scores)
    defense = _average(defense_scores)
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
        + (defense * 0.25)
        + (position_fit * 0.15)
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
        "position_fit": position_fit,
        "balance": round(balance, 2),
        "synergy": synergy,
    }


def build_recommendation_text(metrics):
    metric_labels = {
        "attack": "공격 기대값",
        "midfield": "중원 장악력",
        "defense": "수비 안정성",
        "position_fit": "포지션 적합도",
        "balance": "좌우 밸런스",
        "synergy": "선수 시너지",
    }

    target_keys = list(metric_labels.keys())
    weakest_key = min(target_keys, key=lambda key: safe_number(metrics, key))
    weakest_label = metric_labels[weakest_key]

    advice = {
        "attack": "결정력과 찬스 생산성이 높은 공격 자원을 우선 배치해 보세요.",
        "midfield": "패스 전개와 활동량이 좋은 미드필더를 중심으로 중원을 보강해 보세요.",
        "defense": "수비 지표와 피지컬이 높은 선수를 후방에 우선 배치해 보세요.",
        "position_fit": "선수의 실제 역할과 포메이션 슬롯이 더 잘 맞도록 재배치해 보세요.",
        "balance": "좌우 측면의 전력 차이가 크므로 반대편 측면 자원을 보강해 보세요.",
        "synergy": "라인 간 밸런스를 맞추기 위해 중원과 수비 조합을 함께 조정해 보세요.",
    }

    return f"현재 라인업의 가장 큰 보완 포인트는 {weakest_label}입니다. {advice[weakest_key]}"