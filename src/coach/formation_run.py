from src.coach.formations import FORMATIONS


def load_formations():
    return FORMATIONS


def get_available_formations():
    return list(FORMATIONS.keys())


def get_formation_slots(formation_name):
    if formation_name not in FORMATIONS:
        raise ValueError(f"지원하지 않는 포메이션입니다: {formation_name}")

    return FORMATIONS[formation_name]


def get_formation_positions(formation_name):
    slots = get_formation_slots(formation_name)
    return [slot["role"] for slot in slots]