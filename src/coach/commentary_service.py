from __future__ import annotations

import logging
from typing import Any

from services.azure_config import has_secret

from src.coach.ai_commentary import (
    generate_ai_commentary,
)

from src.coach.local_commentary import (
    generate_local_commentary,
)


logger = logging.getLogger(__name__)


REQUIRED_AZURE_OPENAI_KEYS = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
]


def _azure_openai_ready() -> bool:
    """
    Azure OpenAI 실행에 필요한 설정이
    모두 존재하는지 확인합니다.
    """

    return all(has_secret(key) for key in REQUIRED_AZURE_OPENAI_KEYS)


def _has_selected_player(
    slots: list[dict],
) -> bool:
    """
    현재 라인업에 실제 배치된 선수가
    한 명이라도 있는지 확인합니다.
    """

    return any(slot.get("player") for slot in slots)


def build_commentary(
    formation: str,
    slots: list[dict],
    metrics: dict[str, Any],
) -> dict[str, str | None]:
    """
    코멘트 생성 전략을 결정합니다.

    1. 빈 라인업
       → Local 안내 문구

    2. Azure 설정 없음
       → Local 규칙 기반 코멘트

    3. Azure 설정 있음
       → Azure OpenAI 코멘트

    4. Azure 호출 실패
       → Local 규칙 기반 코멘트로 fallback
    """

    # Local 코멘트는 fallback을 위해
    # 항상 생성 가능하도록 유지합니다.
    local_comment = generate_local_commentary(
        formation=formation,
        slots=slots,
        metrics=metrics,
    )

    # ---------------------------------
    # 1. 빈 라인업
    # ---------------------------------
    if not _has_selected_player(slots):
        return {
            "aiComment": local_comment,
            "fallbackComment": local_comment,
            "commentSource": "empty_lineup",
            "commentError": None,
            "promptPreview": None,
        }

    # ---------------------------------
    # 2. Azure 설정 없음
    #    → Local만 실행
    # ---------------------------------
    if not _azure_openai_ready():
        return {
            "aiComment": local_comment,
            "fallbackComment": local_comment,
            "commentSource": "local",
            "commentError": None,
            "promptPreview": None,
        }

    # ---------------------------------
    # 3. Azure 설정 있음
    # ---------------------------------
    try:
        ai_comment, prompt_preview = generate_ai_commentary(
            formation=formation,
            slots=slots,
            metrics=metrics,
        )

        return {
            "aiComment": ai_comment,
            "fallbackComment": local_comment,
            "commentSource": "azure_openai",
            "commentError": None,
            "promptPreview": prompt_preview,
        }

    # ---------------------------------
    # 4. Azure 실패
    #    → Local fallback
    # ---------------------------------
    except Exception as exc:
        error_name = type(exc).__name__

        logger.warning(
            "Azure OpenAI commentary failed: %s",
            error_name,
        )

        return {
            "aiComment": local_comment,
            "fallbackComment": local_comment,
            "commentSource": "local_after_azure_error",
            "commentError": error_name,
            "promptPreview": None,
        }
