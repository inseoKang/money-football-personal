from __future__ import annotations

import os
from typing import Any

import requests


AZURE_OPENAI_ENDPOINT_ENV = "AZURE_OPENAI_ENDPOINT"
AZURE_OPENAI_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
AZURE_OPENAI_DEPLOYMENT_ENV = "AZURE_OPENAI_DEPLOYMENT"
AZURE_OPENAI_API_VERSION_ENV = "AZURE_OPENAI_API_VERSION"

DEFAULT_API_VERSION = "2024-02-15-preview"


class AzureOpenAIConfigError(RuntimeError):
    pass


def _get_config() -> dict[str, str]:
    endpoint = os.getenv(AZURE_OPENAI_ENDPOINT_ENV, "").rstrip("/")
    api_key = os.getenv(AZURE_OPENAI_API_KEY_ENV, "")
    deployment = os.getenv(AZURE_OPENAI_DEPLOYMENT_ENV, "")
    api_version = os.getenv(AZURE_OPENAI_API_VERSION_ENV, DEFAULT_API_VERSION)

    missing = []
    if not endpoint:
        missing.append(AZURE_OPENAI_ENDPOINT_ENV)
    if not api_key:
        missing.append(AZURE_OPENAI_API_KEY_ENV)
    if not deployment:
        missing.append(AZURE_OPENAI_DEPLOYMENT_ENV)

    if missing:
        raise AzureOpenAIConfigError("Missing Azure OpenAI settings: " + ", ".join(missing))

    return {
        "endpoint": endpoint,
        "api_key": api_key,
        "deployment": deployment,
        "api_version": api_version,
    }


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


def _weakest_metric(metrics: dict[str, Any]) -> str:
    target_keys = ["attack", "midfield", "defense", "keeper", "position_fit", "balance", "synergy"]
    return min(target_keys, key=lambda key: float(metrics.get(key, 0) or 0))


def build_lineup_prompt(formation: str, slots: list[dict], metrics: dict[str, Any]) -> str:
    weakest_key = _weakest_metric(metrics)
    lineup_lines = []

    for slot in slots:
        player = slot.get("player")
        if not player:
            lineup_lines.append(f"- {slot.get('slotId')}: 미배치")
            continue
        lineup_lines.append(
            f"- {slot.get('slotId')}({slot.get('role')}): "
            f"{player.get('name')} / {player.get('positionGroup')} / "
            f"종합 {player.get('scores', {}).get('overall')} / "
            f"역할적합 {slot.get('roleFitScore')}"
        )

    metric_lines = [
        f"- 전체 점수: {metrics.get('team_score')}",
        f"- 공격력: {metrics.get('attack')}",
        f"- 중원 장악력: {metrics.get('midfield')}",
        f"- 수비 안정성: {metrics.get('defense')}",
        f"- 골키퍼 안정성: {metrics.get('keeper')}",
        f"- 포지션 적합도: {metrics.get('position_fit')}",
        f"- 좌우 밸런스: {metrics.get('balance')}",
        f"- 선수 시너지: {metrics.get('synergy')}",
        f"- 가장 낮은 지표: {_metric_label(weakest_key)}",
    ]

    return "\n".join(
        [
            "너는 축구 전술 분석가다.",
            "아래 라인업과 팀 지표를 바탕으로 감독에게 줄 전술 코멘트를 작성해라.",
            "",
            f"포메이션: {formation}",
            "",
            "라인업:",
            *lineup_lines,
            "",
            "팀 지표:",
            *metric_lines,
            "",
            "작성 조건:",
            "- 한국어로 작성",
            "- 3문장 이내",
            "- 가장 부족한 지표를 먼저 언급",
            "- 구체적인 개선 방향 제시",
            "- 과장하지 말 것",
            "- 숫자를 억지로 많이 반복하지 말 것",
        ]
    )


def request_azure_openai_comment(prompt: str, timeout_seconds: int = 20) -> str:
    config = _get_config()
    url = (
        f"{config['endpoint']}/openai/deployments/{config['deployment']}"
        f"/chat/completions?api-version={config['api_version']}"
    )
    headers = {
        "api-key": config["api_key"],
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a concise football tactics analyst for a coach dashboard.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 260,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def build_ai_commentary(formation: str, slots: list[dict], metrics: dict[str, Any], fallback: str) -> dict[str, str]:
    prompt = build_lineup_prompt(formation, slots, metrics)

    try:
        ai_comment = request_azure_openai_comment(prompt)
        return {
            "aiComment": ai_comment,
            "fallbackComment": fallback,
            "commentSource": "azure_openai",
            "commentError": "",
            "promptPreview": prompt,
        }
    except Exception as exc:
        return {
            "aiComment": fallback,
            "fallbackComment": fallback,
            "commentSource": "fallback",
            "commentError": str(exc),
            "promptPreview": prompt,
        }
