from __future__ import annotations

from pathlib import Path
from typing import Any

from services.azure_config import has_secret
from services.azure_openai_service import generate_comment


REQUIRED_AZURE_OPENAI_KEYS = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
]

BASE_DIR = Path(__file__).resolve().parents[2]
PROMPT_PATH = BASE_DIR / "prompts" / "coach_comment_prompt.txt"

DEFAULT_SYSTEM_PROMPT = """
당신은 축구 감독을 보조하는 AI 전술 코치입니다.
입력으로 제공되는 포메이션, 선발 선수, 팀 지표를 바탕으로 다음 형식의 짧은 한국어 코멘트를 작성하세요.

1. 현재 라인업의 강점 1개
2. 현재 라인업의 약점 1개
3. 교체 또는 보완 추천 1개

주의사항:
- 실제 감독처럼 단정적이지만 과장하지 않습니다.
- 데이터에 없는 사실은 말하지 않습니다.
- 3문장 이내로 작성합니다.
""".strip()


def _load_system_prompt() -> str:
    try:
        if PROMPT_PATH.exists():
            content = PROMPT_PATH.read_text(encoding="utf-8").strip()
            if content:
                return content
    except Exception:
        pass

    return DEFAULT_SYSTEM_PROMPT


def _metric_label(key: str) -> str:
    labels = {
        "attack": "공격력",
        "midfield": "중원 장악력",
        "defense": "수비 안정성",
        "keeper": "골키퍼 안정성",
        "position_fit": "포지션 적합도",
        "balance": "좌우 밸런스",
        "synergy": "선수 시너지",
    }
    return labels.get(key, key)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in [None, ""]:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _weakest_metric(metrics: dict[str, Any]) -> str:
    target_keys = [
        "attack",
        "midfield",
        "defense",
        "keeper",
        "position_fit",
        "balance",
        "synergy",
    ]

    return min(
        target_keys,
        key=lambda key: _safe_float(metrics.get(key), 0.0),
    )


def _strongest_metric(metrics: dict[str, Any]) -> str:
    target_keys = [
        "attack",
        "midfield",
        "defense",
        "keeper",
        "position_fit",
        "balance",
        "synergy",
    ]

    return max(
        target_keys,
        key=lambda key: _safe_float(metrics.get(key), 0.0),
    )


def _azure_openai_ready() -> bool:
    return all(has_secret(key) for key in REQUIRED_AZURE_OPENAI_KEYS)


def build_lineup_prompt(
    formation: str,
    slots: list[dict],
    metrics: dict[str, Any],
) -> str:
    weakest_key = _weakest_metric(metrics)
    strongest_key = _strongest_metric(metrics)

    lineup_lines = []

    for slot in slots:
        player = slot.get("player")

        if not player:
            lineup_lines.append(f"- {slot.get('slotId')}: 미배치")
            continue

        scores = player.get("scores", {}) or {}
        stats = player.get("stats", {}) or {}

        lineup_lines.append(
            f"- {slot.get('slotId')}({slot.get('role')}): "
            f"{player.get('name')} / {player.get('positionGroup')} / "
            f"종합 {scores.get('overall')} / "
            f"공격 {scores.get('attack')} / "
            f"수비 {scores.get('defense')} / "
            f"골키퍼 {scores.get('keeper')} / "
            f"활동량 {scores.get('stamina')} / "
            f"규율 {scores.get('discipline')} / "
            f"역할적합 {slot.get('roleFitScore')} / "
            f"출전 {stats.get('matches')}경기 / "
            f"득점 {stats.get('goals')} / 도움 {stats.get('assists')}"
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
        f"- 가장 강한 지표: {_metric_label(strongest_key)}",
        f"- 가장 약한 지표: {_metric_label(weakest_key)}",
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


def build_ai_commentary(
    formation: str,
    slots: list[dict],
    metrics: dict[str, Any],
    fallback: str,
) -> dict[str, str | None]:
    system_prompt = _load_system_prompt()
    user_prompt = build_lineup_prompt(formation, slots, metrics)

    if not _azure_openai_ready():
        return {
            "aiComment": fallback,
            "fallbackComment": fallback,
            "commentSource": "fallback_missing_azure_openai",
            "commentError": "Azure OpenAI settings are missing.",
            "promptPreview": user_prompt,
        }

    try:
        ai_comment = generate_comment(
            user_prompt,
            system_prompt=system_prompt,
        )

        return {
            "aiComment": ai_comment,
            "fallbackComment": fallback,
            "commentSource": "azure_openai",
            "commentError": None,
            "promptPreview": user_prompt,
        }

    except Exception as exc:
        return {
            "aiComment": fallback,
            "fallbackComment": fallback,
            "commentSource": "fallback_error",
            "commentError": str(exc),
            "promptPreview": user_prompt,
        }