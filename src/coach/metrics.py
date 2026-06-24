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


def _empty_team_metrics():
    """
    아직 라인업에 선수가 한 명도 배치되지 않았을 때 반환할 기본 지표입니다.

    빈 라인업 상태에서는 좌우 밸런스, 선수 시너지, 팀 종합 점수 모두
    평가할 수 없으므로 0으로 처리합니다.
    """
    return {
        "team_score": 0,
        "grade": "D",
        "attack": 0,
        "midfield": 0,
        "defense": 0,
        "keeper": 0,
        "position_fit": 0,
        "balance": 0,
        "synergy": 0,
    }


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

    # 핵심 수정:
    # 실제로 배치된 선수가 한 명도 없으면 모든 지표를 0으로 반환합니다.
    # 기존에는 balance 기본값 75 때문에 빈 라인업에서도
    # synergy 15, team_score 약 4점이 계산되는 문제가 있었습니다.
    if not position_fit_scores:
        return _empty_team_metrics()

    attack = _average(attack_scores)
    midfield = _average(midfield_scores)
    defense = _average(defense_scores)
    keeper = _average(keeper_scores)
    position_fit = _average(position_fit_scores)

    # 좌우 양쪽에 선수가 모두 있어야 좌우 밸런스를 계산합니다.
    # 한쪽만 있거나 양쪽 모두 없으면 아직 밸런스를 평가할 수 없으므로 0점 처리합니다.
    if left_scores and right_scores:
        balance = 100 - abs(_average(left_scores) - _average(right_scores))
    else:
        balance = 0

    balance = max(0, min(100, balance))

    # 시너지는 실제 배치된 선수들의 포지션 적합도, 밸런스, 중원/수비 지표를 기반으로 계산합니다.
    synergy = round(
        (position_fit * 0.5)
        + (balance * 0.2)
        + (midfield * 0.15)
        + (defense * 0.15),
        2,
    )

    synergy = max(0, min(100, synergy))

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

    team_score = max(0, min(100, team_score))

    return {
        "team_score": team_score,
        "grade": _grade(team_score),
        "attack": attack,
        "midfield": midfield,
        "defense": defense,
        "keeper": keeper,
        "position_fit": position_fit,
        "balance": round(balance, 2),
        "synergy": round(synergy, 2),
    }


def build_recommendation_text(metrics):
    # 빈 라인업 상태에서는 약점 분석 문구를 띄우지 않습니다.
    if not metrics or safe_number(metrics, "team_score", 0) == 0:
        return (
            "아직 선택된 선수가 없습니다. "
            "포지션 슬롯을 클릭해 선수를 배치하면 팀 지표와 추천 개선 사항이 표시됩니다."
        )

    metric_labels = {
        "attack": "공격 기대값",
        "midfield": "중원 장악력",
        "defense": "수비 안정성",
        "keeper": "골키퍼 안정성",
        "position_fit": "포지션 적합도",
        "balance": "좌우 밸런스",
        "synergy": "선수 시너지",
    }

    advice = {
        "attack": "마무리 능력, 슈팅 생산성, 득점 기여도가 높은 공격 자원을 보강하거나 전진 배치하는 것이 좋습니다.",
        "midfield": "활동량과 공수 연결 능력이 좋은 미드필더를 중심으로 중원 구성을 조정하는 것이 좋습니다.",
        "defense": "태클, 인터셉트, 수비 집중력이 높은 수비수를 우선적으로 배치하는 것이 좋습니다.",
        "keeper": "선방 능력과 안정성이 높은 골키퍼를 확인하고, 필요하다면 골키퍼 교체를 고려하는 것이 좋습니다.",
        "position_fit": "선수들이 각자의 강점과 맞는 포지션에 배치되어 있는지 다시 확인하는 것이 좋습니다.",
        "balance": "좌우 전력 균형이 맞지 않습니다. 약한 측면을 보강하거나 측면 역할을 조정하는 것이 좋습니다.",
        "synergy": "선수 간 조합이 아직 충분히 안정적이지 않습니다. 중원, 수비, 포지션 적합도의 균형을 함께 조정하는 것이 좋습니다.",
    }

    target_keys = list(metric_labels.keys())
    weakest_key = min(target_keys, key=lambda key: safe_number(metrics, key, 0))
    weakest_label = metric_labels[weakest_key]

    return (
        f"현재 라인업에서 가장 보완이 필요한 부분은 {weakest_label}입니다. "
        f"{advice[weakest_key]}"
    )