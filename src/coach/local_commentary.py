from __future__ import annotations

from typing import Any


METRIC_LABELS = {
    "attack": "공격력",
    "midfield": "중원 장악력",
    "defense": "수비 안정성",
    "keeper": "골키퍼 안정성",
    "position_fit": "포지션 적합도",
    "balance": "좌우 밸런스",
    "synergy": "선수 시너지",
}

METRIC_KEYS = list(METRIC_LABELS.keys())


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value in (None, ""):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _score_level(score: float) -> str:
    if score >= 85:
        return "매우 안정적인 수준"

    if score >= 75:
        return "좋은 수준"

    if score >= 65:
        return "무난한 수준"

    if score >= 50:
        return "다소 보완이 필요한 수준"

    return "우선적인 개선이 필요한 수준"


def _strongest_metric(
    metrics: dict[str, Any],
) -> str:
    return max(
        METRIC_KEYS,
        key=lambda key: _safe_float(metrics.get(key)),
    )


def _weakest_metric(
    metrics: dict[str, Any],
) -> str:
    return min(
        METRIC_KEYS,
        key=lambda key: _safe_float(metrics.get(key)),
    )


def _find_position_mismatches(
    slots: list[dict],
    threshold: float = 70,
) -> list[dict]:
    """
    roleFitScore가 낮은 선수를 찾습니다.
    """

    mismatches = []

    for slot in slots:
        player = slot.get("player")

        if not player:
            continue

        role_fit_score = _safe_float(
            slot.get("roleFitScore"),
            100,
        )

        if role_fit_score >= threshold:
            continue

        mismatches.append(
            {
                "name": player.get(
                    "name",
                    "선수",
                ),
                "role": slot.get(
                    "role",
                    slot.get(
                        "slotId",
                        "현재 포지션",
                    ),
                ),
                "position_group": player.get(
                    "positionGroup",
                    "알 수 없음",
                ),
                "role_fit_score": role_fit_score,
            }
        )

    return mismatches


def _find_goalkeeper(
    slots: list[dict],
) -> dict | None:
    for slot in slots:
        player = slot.get("player")

        if not player:
            continue

        role = str(slot.get("role") or slot.get("slotId") or "").upper()

        if role == "GK":
            return player

    return None


def _build_recommendation(
    weakest_key: str,
    slots: list[dict],
) -> str:
    if weakest_key == "keeper":
        goalkeeper = _find_goalkeeper(slots)

        if goalkeeper:
            goalkeeper_name = goalkeeper.get(
                "name",
                "현재 골키퍼",
            )

            return (
                f"현재 골키퍼 {goalkeeper_name}와 다른 후보의 "
                "골키퍼 관련 지표를 비교해 선발 변경 여부를 "
                "우선 검토하는 것이 좋습니다."
            )

        return "골키퍼 후보들의 관련 지표를 비교해 선발 구성을 우선 검토하는 것이 좋습니다."

    recommendation_map = {
        "attack": (
            "공격 기여도가 높은 선수 조합을 검토하고 공격진의 배치와 역할을 조정하는 것이 좋습니다."
        ),
        "midfield": (
            "중원에서 볼 연결과 활동량이 좋은 선수의 비중을 높여 "
            "경기 주도권을 보완하는 것이 좋습니다."
        ),
        "defense": (
            "수비력이 높은 선수 중심으로 수비 라인을 조정해 후방 안정성을 높이는 것이 좋습니다."
        ),
        "position_fit": (
            "주 포지션과 실제 배치 위치가 다른 선수가 있는지 확인하고 "
            "포지션 적합도가 높은 배치를 우선 고려하는 것이 좋습니다."
        ),
        "balance": (
            "좌우 측면의 선수 구성과 역할을 다시 조정해 공격과 수비의 균형을 맞추는 것이 좋습니다."
        ),
        "synergy": (
            "개별 능력치뿐 아니라 선수 간 역할 조합을 고려해 "
            "라인업 일부를 재구성하는 것이 좋습니다."
        ),
    }

    return recommendation_map.get(
        weakest_key,
        ("가장 낮은 팀 지표를 중심으로 라인업 구성을 보완하는 것이 좋습니다."),
    )


def generate_local_commentary(
    formation: str,
    slots: list[dict],
    metrics: dict[str, Any],
) -> str:
    """
    외부 LLM 없이 현재 라인업 데이터를 기반으로
    규칙 기반 감독 코멘트를 생성합니다.

    출력:
        강점 1문장
        약점 1문장
        추천 1문장
    """

    team_score = _safe_float(
        metrics.get("team_score"),
        0,
    )

    if team_score <= 0:
        return (
            "아직 분석할 수 있는 라인업 데이터가 충분하지 않습니다. "
            "선수를 배치한 뒤 다시 확인해 주세요."
        )

    strongest_key = _strongest_metric(metrics)
    weakest_key = _weakest_metric(metrics)

    strongest_score = _safe_float(metrics.get(strongest_key))

    weakest_score = _safe_float(metrics.get(weakest_key))

    strongest_label = METRIC_LABELS[strongest_key]

    weakest_label = METRIC_LABELS[weakest_key]

    # 1문장: 강점
    strength_comment = (
        f"현재 {formation} 라인업은 "
        f"{strongest_label}가 {strongest_score:.0f}점으로 가장 높으며 "
        f"{_score_level(strongest_score)}입니다."
    )

    # 2문장: 약점
    weakness_comment = (
        f"반면 {weakest_label}은(는) "
        f"{weakest_score:.0f}점으로 가장 낮아 "
        f"{_score_level(weakest_score)}입니다."
    )

    # 역할 적합도가 낮은 선수가 있으면
    # 새로운 문장을 추가하지 않고 약점 문장 안에 포함
    mismatches = _find_position_mismatches(slots)

    if mismatches:
        mismatch = mismatches[0]

        weakness_comment = (
            f"반면 {weakest_label}은(는) "
            f"{weakest_score:.0f}점으로 가장 낮고, "
            f"{mismatch['name']} 선수의 "
            f"{mismatch['role']} 배치 역할 적합도도 "
            f"{mismatch['role_fit_score']:.0f}점으로 "
            "보완이 필요합니다."
        )

    # 3문장: 추천
    recommendation = _build_recommendation(
        weakest_key,
        slots,
    )

    return " ".join(
        [
            strength_comment,
            weakness_comment,
            recommendation,
        ]
    )
