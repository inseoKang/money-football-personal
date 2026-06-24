from src.coach.config import COLUMN_MAP


def validate_player_columns(players):
    required_columns = set(COLUMN_MAP.values())
    actual_columns = set(players.columns)

    missing_columns = required_columns - actual_columns

    if missing_columns:
        raise ValueError(
            "선수 데이터에 필요한 컬럼이 없습니다: "
            + ", ".join(sorted(missing_columns))
        )