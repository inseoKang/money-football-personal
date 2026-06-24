"""Azure OpenAI commentary helpers for deployment smoke tests."""

from __future__ import annotations

from typing import Any

from services.azure_config import get_secret


AZURE_OPENAI_ENDPOINT = "AZURE_OPENAI_ENDPOINT"
AZURE_OPENAI_API_KEY = "AZURE_OPENAI_API_KEY"
AZURE_OPENAI_DEPLOYMENT = "AZURE_OPENAI_DEPLOYMENT"
AZURE_OPENAI_API_VERSION = "AZURE_OPENAI_API_VERSION"
DEFAULT_API_VERSION = "2024-12-01-preview"

DEFAULT_SYSTEM_PROMPT = (
    "You are a football data analyst. Explain concisely using only the provided data, "
    "and avoid exaggerated claims."
)


def _azure_openai_settings() -> dict[str, str]:
    settings = {
        "endpoint": str(get_secret(AZURE_OPENAI_ENDPOINT, "")).rstrip("/"),
        "api_key": str(get_secret(AZURE_OPENAI_API_KEY, "")),
        "deployment": str(get_secret(AZURE_OPENAI_DEPLOYMENT, "")),
        "api_version": str(get_secret(AZURE_OPENAI_API_VERSION, DEFAULT_API_VERSION)),
    }
    missing = [
        env
        for env, key in [
            (AZURE_OPENAI_ENDPOINT, "endpoint"),
            (AZURE_OPENAI_API_KEY, "api_key"),
            (AZURE_OPENAI_DEPLOYMENT, "deployment"),
        ]
        if not settings[key]
    ]
    if missing:
        raise RuntimeError("Missing Azure OpenAI settings: " + ", ".join(missing))
    return settings


def get_azure_openai_client():
    """Return an AzureOpenAI client configured from environment/secrets."""
    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is not installed") from exc

    settings = _azure_openai_settings()
    return AzureOpenAI(
        azure_endpoint=settings["endpoint"],
        api_key=settings["api_key"],
        api_version=settings["api_version"],
    )


def generate_comment(prompt: str, system_prompt: str | None = None) -> str:
    """Generate a short football analysis comment using Azure OpenAI."""
    settings = _azure_openai_settings()
    client = get_azure_openai_client()
    try:
        response = client.chat.completions.create(
            model=settings["deployment"],
            messages=[
                {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise RuntimeError(f"Azure OpenAI request failed: {exc}") from exc


def generate_scout_comment(
    player_name: str,
    position: str,
    current_salary: Any,
    predicted_salary: Any,
    key_stats: Any,
) -> str:
    """Generate a scout-facing salary value explanation."""
    prompt = (
        "Write in Korean within 4 sentences for a football scout.\n"
        f"Player: {player_name}\n"
        f"Position: {position}\n"
        f"Current salary EUR: {current_salary}\n"
        f"Predicted next salary EUR: {predicted_salary}\n"
        f"Key stats: {key_stats}\n"
        "Mention undervaluation if predicted salary is higher than current salary, "
        "or overvaluation if lower. Use cautious, data-based wording."
    )
    return generate_comment(prompt)


def generate_coach_comment(team_name: str, formation: str, team_scores: Any) -> str:
    """Generate a coach-facing tactical comment."""
    prompt = (
        "Write in Korean within 5 sentences for a football coach.\n"
        f"Team: {team_name}\n"
        f"Formation: {formation}\n"
        f"Team scores: {team_scores}\n"
        "Include attack, midfield, defense, formation strengths and weaknesses."
    )
    return generate_comment(prompt)
