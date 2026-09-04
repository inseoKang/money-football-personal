from __future__ import annotations

from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]

PROMPT_PATH = BASE_DIR / "prompts" / "coach_comment_prompt.txt"


# prompt.txt 파일이 없거나 읽기에 실패했을 때 사용할 fallback
DEFAULT_SYSTEM_PROMPT = """
당신은 축구 감독을 보조하는 AI 전술 코치입니다.
입력으로 제공되는 포메이션, 선발 선수, 팀 지표를 바탕으로 다음 형식의 짧은 한국어 코멘트를 작성하세요.

1. 현재 라인업의 강점 1개
2. 현재 라인업의 약점 1개
3. 교체 또는 보완 추천 1개

주의사항:
- 실제 감독처럼 단정적이지만 과장하지 않습니다.
- 데이터에 없는 사실은 말하지 않습니다.
- 반드시 제공된 선수 정보와 팀 지표만 근거로 판단합니다.
- 강점, 약점, 추천을 각각 1문장으로 작성합니다.
- 전체 코멘트는 반드시 3문장 이내로 작성합니다.
""".strip()


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


def _load_system_prompt() -> str:
    """
    prompts/coach_comment_prompt.txt를 읽습니다.

    파일이 없거나 비어 있거나 읽기에 실패하면
    DEFAULT_SYSTEM_PROMPT를 사용합니다.
    """
    try:
        if PROMPT_PATH.exists():
            content = PROMPT_PATH.read_text(encoding="utf-8").strip()

            if content:
                return content

    except Exception:
        pass

    return DEFAULT_SYSTEM_PROMPT


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


def build_lineup_prompt(
    formation: str,
    slots: list[dict],
    metrics: dict[str, Any],
) -> str:
    """
    Azure OpenAI에 전달할 현재 라인업 데이터를
    user prompt 형태로 변환합니다.
    """

    strongest_key = _strongest_metric(metrics)
    weakest_key = _weakest_metric(metrics)

    lineup_lines = []

    for slot in slots:
        player = slot.get("player")

        slot_id = slot.get(
            "slotId",
            "UNKNOWN",
        )

        role = slot.get(
            "role",
            slot_id,
        )

        if not player:
            lineup_lines.append(f"- {slot_id}({role}): 미배치")
            continue

        scores = player.get("scores", {}) or {}
        stats = player.get("stats", {}) or {}

        lineup_lines.append(
            f"- {slot_id}({role}): "
            f"{player.get('name', '이름 없음')} / "
            f"주 포지션 그룹 "
            f"{player.get('positionGroup', '알 수 없음')} / "
            f"종합 {scores.get('overall')} / "
            f"공격 {scores.get('attack')} / "
            f"수비 {scores.get('defense')} / "
            f"골키퍼 {scores.get('keeper')} / "
            f"활동량 {scores.get('stamina')} / "
            f"규율 {scores.get('discipline')} / "
            f"역할적합 {slot.get('roleFitScore')} / "
            f"출전 {stats.get('matches')}경기 / "
            f"득점 {stats.get('goals')} / "
            f"도움 {stats.get('assists')}"
        )

    metric_lines = [
        f"- 팀 종합 점수: {metrics.get('team_score')}",
        f"- 등급: {metrics.get('grade')}",
        f"- 공격력: {metrics.get('attack')}",
        f"- 중원 장악력: {metrics.get('midfield')}",
        f"- 수비 안정성: {metrics.get('defense')}",
        f"- 골키퍼 안정성: {metrics.get('keeper')}",
        f"- 포지션 적합도: {metrics.get('position_fit')}",
        f"- 좌우 밸런스: {metrics.get('balance')}",
        f"- 선수 시너지: {metrics.get('synergy')}",
        (f"- 가장 강한 지표: {METRIC_LABELS[strongest_key]}"),
        (f"- 가장 약한 지표: {METRIC_LABELS[weakest_key]}"),
    ]

    return "\n".join(
        [
            "아래는 현재 라인업 데이터입니다.",
            "반드시 제공된 데이터만 근거로 코멘트를 작성하세요.",
            "",
            f"포메이션: {formation}",
            "",
            "선발 선수:",
            *lineup_lines,
            "",
            "팀 지표:",
            *metric_lines,
        ]
    )


def generate_ai_commentary(
    formation: str,
    slots: list[dict],
    metrics: dict[str, Any],
) -> tuple[str, str]:
    """
    Azure OpenAI를 사용해 코멘트를 생성합니다.

    Azure 관련 모듈은 실제 Azure 호출이 필요할 때만 불러옵니다.
    따라서 Azure 패키지나 설정에 문제가 있어도
    commentary_service에서 Local fallback을 실행할 수 있습니다.

    반환:
        (
            생성된 Azure AI 코멘트,
            실제 Azure에 전달한 user prompt,
        )
    """
    from services.azure_openai_service import generate_comment

    system_prompt = _load_system_prompt()

    user_prompt = build_lineup_prompt(
        formation=formation,
        slots=slots,
        metrics=metrics,
    )

    ai_comment = generate_comment(
        user_prompt,
        system_prompt=system_prompt,
    )

    return ai_comment, user_prompt
