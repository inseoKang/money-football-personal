from __future__ import annotations

from src.coach.commentary_service import build_commentary
from src.coach.formation_run import (
    get_available_formations,
    get_formation_slots,
)
from src.coach.formations import ROLE_ALIASES
from src.coach.player_data import load_manager_players
from src.coach.scoring import (
    is_position_compatible,
    role_score,
)


PLAYER_CARD_COLUMNS = [
    "salary_id",
    "player",
    "club",
    "league",
    "position_group",
    "age",
    "country",
    "overall_score",
    "attack_score",
    "defense_score",
    "keeper_score",
    "stamina_score",
    "discipline_score",
    "matches",
    "minutes",
    "goals",
    "assists",
]


def _candidate_positions(
    role: str,
) -> list[str]:
    return ROLE_ALIASES.get(
        role,
        [role],
    )


def _get_role_candidates(
    players,
    role: str,
    used_salary_ids: set,
):
    available_players = players[~players["salary_id"].isin(used_salary_ids)].copy()

    if available_players.empty:
        return available_players

    compatible_candidates = available_players[
        available_players.apply(
            lambda player: is_position_compatible(
                player,
                role,
            ),
            axis=1,
        )
    ].copy()

    if not compatible_candidates.empty:
        return compatible_candidates

    # RW/LW/ST 같은 공격 슬롯은
    # 전문 포지션 후보가 없어도
    # 전체 미사용 선수 중 role_score 기준으로
    # fallback 추천합니다.
    if role in ["RW", "LW", "ST"]:
        return available_players

    return compatible_candidates


def _player_payload(
    player,
) -> dict:
    return {
        "salaryId": int(player["salary_id"]),
        "name": player["player"],
        "club": player["club"],
        "league": player["league"],
        "positionGroup": player["position_group"],
        "age": int(player["age"]),
        "country": player["country"],
        "scores": {
            "overall": round(
                float(player["overall_score"]),
                2,
            ),
            "attack": round(
                float(player["attack_score"]),
                2,
            ),
            "defense": round(
                float(player["defense_score"]),
                2,
            ),
            "keeper": round(
                float(player["keeper_score"]),
                2,
            ),
            "stamina": round(
                float(player["stamina_score"]),
                2,
            ),
            "discipline": round(
                float(player["discipline_score"]),
                2,
            ),
        },
        "stats": {
            "matches": int(player["matches"]),
            "minutes": int(player["minutes"]),
            "goals": int(player["goals"]),
            "assists": int(player["assists"]),
        },
    }


def get_player_pool_payload(
    players_df=None,
    limit: int | None = None,
) -> list[dict]:
    players = load_manager_players() if players_df is None else players_df.copy()

    players = players.sort_values(
        "overall_score",
        ascending=False,
    )

    if limit:
        players = players.head(limit)

    return [_player_payload(player) for _, player in players[PLAYER_CARD_COLUMNS].iterrows()]


def get_formation_payload(
    formation: str,
) -> dict:
    slots = []

    for slot in get_formation_slots(formation):
        slots.append(
            {
                "slotId": slot["slot_id"],
                "role": slot["role"],
                "line": slot["line"],
                "x": slot["x"],
                "y": slot["y"],
                "acceptedPositions": (_candidate_positions(slot["role"])),
            }
        )

    return {
        "formation": formation,
        "slots": slots,
    }


def get_formations_payload() -> list[dict]:
    return [get_formation_payload(formation) for formation in get_available_formations()]


def recommend_lineup_payload(
    players_df=None,
    formation: str = "4-3-3",
) -> dict:
    players = load_manager_players() if players_df is None else players_df.copy()

    used_salary_ids = set()
    lineup = {}

    for slot in get_formation_slots(formation):
        role = slot["role"]

        candidates = _get_role_candidates(
            players=players,
            role=role,
            used_salary_ids=used_salary_ids,
        )

        if candidates.empty:
            lineup[slot["slot_id"]] = None
            continue

        candidates["roleFitScore"] = candidates.apply(
            lambda player: role_score(
                player,
                role,
            ),
            axis=1,
        )

        best = candidates.sort_values(
            "roleFitScore",
            ascending=False,
        ).iloc[0]

        salary_id = int(best["salary_id"])

        used_salary_ids.add(salary_id)

        lineup[slot["slot_id"]] = salary_id

    return evaluate_lineup_payload(
        players,
        formation,
        lineup,
    )


def evaluate_lineup_payload(
    players_df,
    formation: str,
    lineup: dict,
) -> dict:
    players = players_df.copy()

    player_by_id = {int(player["salary_id"]): player for _, player in players.iterrows()}

    slot_payloads = []

    attack_scores = []
    midfield_scores = []
    defense_scores = []
    keeper_scores = []
    position_fit_scores = []
    left_scores = []
    right_scores = []

    warnings = []

    for slot in get_formation_slots(formation):
        slot_id = slot["slot_id"]
        role = slot["role"]
        line = slot["line"]

        salary_id = lineup.get(slot_id)

        player = player_by_id.get(int(salary_id)) if salary_id else None

        if player is None:
            warnings.append(f"{slot_id} 슬롯이 비어 있습니다.")

            slot_payloads.append(
                {
                    "slotId": slot_id,
                    "role": role,
                    "line": line,
                    "x": slot["x"],
                    "y": slot["y"],
                    "acceptedPositions": (_candidate_positions(role)),
                    "player": None,
                    "roleFitScore": 0,
                }
            )

            continue

        fit_score = role_score(
            player,
            role,
        )

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

        accepted_positions = _candidate_positions(role)

        if player["position_group"] not in accepted_positions:
            warnings.append(
                f"{player['player']} 선수가 "
                f"{slot_id} 슬롯에 배치되었지만, "
                "주 포지션 그룹은 "
                f"{player['position_group']}입니다."
            )

        slot_payloads.append(
            {
                "slotId": slot_id,
                "role": role,
                "line": line,
                "x": slot["x"],
                "y": slot["y"],
                "acceptedPositions": (accepted_positions),
                "player": (_player_payload(player)),
                "roleFitScore": (fit_score),
            }
        )

    metrics = _build_metrics(
        attack_scores,
        midfield_scores,
        defense_scores,
        keeper_scores,
        position_fit_scores,
        left_scores,
        right_scores,
    )

    # 코멘트 생성 정책은
    # commentary_service가 전부 담당합니다.
    commentary = build_commentary(
        formation=formation,
        slots=slot_payloads,
        metrics=metrics,
    )

    return {
        "formation": formation,
        "lineup": lineup,
        "slots": slot_payloads,
        "metrics": metrics,
        "aiComment": commentary["aiComment"],
        "fallbackComment": commentary["fallbackComment"],
        "commentSource": commentary["commentSource"],
        "commentError": commentary["commentError"],
        "promptPreview": commentary["promptPreview"],
        "warnings": warnings,
    }


def _average(
    values: list[float],
) -> float:
    clean = [float(value) for value in values if value is not None]

    if not clean:
        return 0.0

    return round(
        sum(clean) / len(clean),
        2,
    )


def _grade(
    score: float,
) -> str:
    if score >= 90:
        return "S"

    if score >= 80:
        return "A"

    if score >= 70:
        return "B"

    if score >= 60:
        return "C"

    return "D"


def _empty_team_metrics() -> dict:
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


def _build_metrics(
    attack_scores,
    midfield_scores,
    defense_scores,
    keeper_scores,
    position_fit_scores,
    left_scores,
    right_scores,
) -> dict:
    # 실제 배치된 선수가 한 명도 없다면
    # 모든 지표를 0으로 처리합니다.
    if not position_fit_scores:
        return _empty_team_metrics()

    attack = _average(attack_scores)

    midfield = _average(midfield_scores)

    defense = _average(defense_scores)

    keeper = _average(keeper_scores)

    position_fit = _average(position_fit_scores)

    # 좌우 양쪽에 선수가 있을 때만
    # 밸런스를 계산합니다.
    if left_scores and right_scores:
        balance = 100 - abs(_average(left_scores) - _average(right_scores))
    else:
        balance = 0

    balance = max(
        0,
        min(
            100,
            balance,
        ),
    )

    synergy = round(
        (position_fit * 0.5) + (balance * 0.2) + (midfield * 0.15) + (defense * 0.15),
        2,
    )

    synergy = max(
        0,
        min(
            100,
            synergy,
        ),
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

    team_score = max(
        0,
        min(
            100,
            team_score,
        ),
    )

    return {
        "team_score": team_score,
        "grade": _grade(team_score),
        "attack": attack,
        "midfield": midfield,
        "defense": defense,
        "keeper": keeper,
        "position_fit": position_fit,
        "balance": round(
            balance,
            2,
        ),
        "synergy": round(
            synergy,
            2,
        ),
    }
