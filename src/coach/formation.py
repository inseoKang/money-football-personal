import json

from src.coach.config import FORMATIONS_FILE


def load_formations():
    with open(FORMATIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_available_formations():
    formations = load_formations()
    return list(formations.keys())


def get_formation_positions(formation_name):
    formations = load_formations()

    if formation_name not in formations:
        raise ValueError(f"지원하지 않는 포메이션입니다: {formation_name}")

    return formations[formation_name]