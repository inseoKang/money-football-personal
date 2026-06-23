from pathlib import Path

import pandas as pd

from src.coach.config import BASE_DIR


MANAGER_PLAYER_COLUMNS = [
    "salary_id",
    "player",
    "club",
    "league",
    "season",
    "position",
    "position_group",
    "age",
    "country",
    "active",
    "loan",
    "matches",
    "starts",
    "minutes",
    "nineties",
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "interceptions",
    "tackles_won",
    "saves",
    "save_pct",
    "clean_sheets",
    "yellow_cards",
    "red_cards",
]

NUMERIC_COLUMNS = [
    "salary_id",
    "age",
    "matches",
    "starts",
    "minutes",
    "nineties",
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "interceptions",
    "tackles_won",
    "saves",
    "save_pct",
    "clean_sheets",
    "yellow_cards",
    "red_cards",
]

BOOLEAN_COLUMNS = ["active", "loan"]

DEFAULT_MANAGER_DATA_FILES = [
    BASE_DIR / "data" / "manager_players.xlsx",
    BASE_DIR / "data" / "manager_players.csv",
    BASE_DIR / "data" / "25-26_merged_manager_raw_data.xlsx",
]


def _first_existing_data_file():
    for path in DEFAULT_MANAGER_DATA_FILES:
        if path.exists():
            return path
    return BASE_DIR / "data" / "sample_players.csv"


def _read_data_file(path):
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def _normalize_position_group(value):
    if pd.isna(value):
        return "UNK"

    text = str(value).upper().strip()
    if text == "K":
        return "GK"
    if text in {"GK", "DF", "MF", "FW"}:
        return text
    if "GK" in text or "KEEPER" in text:
        return "GK"
    if any(token in text for token in ["DF", "CB", "LB", "RB", "WB", "D"]):
        return "DF"
    if any(token in text for token in ["MF", "CM", "DM", "AM", "M"]):
        return "MF"
    if any(token in text for token in ["FW", "ST", "CF", "LW", "RW", "F"]):
        return "FW"
    return text


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _percentile_score(series, higher_is_better=True):
    values = pd.to_numeric(series, errors="coerce").fillna(0)
    if values.nunique() <= 1:
        return pd.Series(50.0, index=series.index)

    score = values.rank(pct=True) * 100
    if not higher_is_better:
        score = 101 - score
    return score.clip(0, 100).round(2)


def _weighted_average(df, weights):
    total = pd.Series(0.0, index=df.index)
    total_weight = 0

    for column, weight in weights.items():
        if column not in df.columns:
            continue
        total += df[column].fillna(0) * weight
        total_weight += weight

    if total_weight == 0:
        return pd.Series(0.0, index=df.index)

    return (total / total_weight).clip(0, 100).round(2)


def select_manager_columns(players):
    output = players.copy()

    for column in MANAGER_PLAYER_COLUMNS:
        if column not in output.columns:
            output[column] = None

    output = output[MANAGER_PLAYER_COLUMNS].copy()

    output["position_group"] = output["position_group"].map(_normalize_position_group)

    for column in NUMERIC_COLUMNS:
        output[column] = pd.to_numeric(output[column], errors="coerce").fillna(0)

    for column in BOOLEAN_COLUMNS:
        output[column] = output[column].map(_to_bool)

    output["salary_id"] = output["salary_id"].astype(int)
    output["age"] = output["age"].astype(int)
    output["matches"] = output["matches"].astype(int)
    output["starts"] = output["starts"].astype(int)
    output["minutes"] = output["minutes"].astype(int)
    output["goals"] = output["goals"].astype(int)
    output["assists"] = output["assists"].astype(int)
    output["shots"] = output["shots"].astype(int)
    output["shots_on_target"] = output["shots_on_target"].astype(int)
    output["interceptions"] = output["interceptions"].astype(int)
    output["tackles_won"] = output["tackles_won"].astype(int)
    output["saves"] = output["saves"].astype(int)
    output["clean_sheets"] = output["clean_sheets"].astype(int)
    output["yellow_cards"] = output["yellow_cards"].astype(int)
    output["red_cards"] = output["red_cards"].astype(int)

    return output


def add_manager_scores(players):
    scored = players.copy()

    scored["_goal_score"] = _percentile_score(scored["goals"])
    scored["_assist_score"] = _percentile_score(scored["assists"])
    scored["_shot_score"] = _percentile_score(scored["shots"])
    scored["_shot_target_score"] = _percentile_score(scored["shots_on_target"])
    scored["_interception_score"] = _percentile_score(scored["interceptions"])
    scored["_tackle_score"] = _percentile_score(scored["tackles_won"])
    scored["_save_score"] = _percentile_score(scored["saves"])
    scored["_save_pct_score"] = _percentile_score(scored["save_pct"])
    scored["_clean_sheet_score"] = _percentile_score(scored["clean_sheets"])
    scored["_match_score"] = _percentile_score(scored["matches"])
    scored["_start_score"] = _percentile_score(scored["starts"])
    scored["_minute_score"] = _percentile_score(scored["minutes"])
    scored["_yellow_card_score"] = _percentile_score(scored["yellow_cards"], higher_is_better=False)
    scored["_red_card_score"] = _percentile_score(scored["red_cards"], higher_is_better=False)

    scored["attack_score"] = _weighted_average(
        scored,
        {
            "_goal_score": 0.35,
            "_assist_score": 0.20,
            "_shot_target_score": 0.25,
            "_shot_score": 0.20,
        },
    )
    scored["defense_score"] = _weighted_average(
        scored,
        {
            "_interception_score": 0.55,
            "_tackle_score": 0.45,
        },
    )
    scored["keeper_score"] = _weighted_average(
        scored,
        {
            "_save_score": 0.35,
            "_save_pct_score": 0.35,
            "_clean_sheet_score": 0.30,
        },
    )
    scored["stamina_score"] = _weighted_average(
        scored,
        {
            "_minute_score": 0.50,
            "_start_score": 0.30,
            "_match_score": 0.20,
        },
    )
    scored["discipline_score"] = _weighted_average(
        scored,
        {
            "_yellow_card_score": 0.55,
            "_red_card_score": 0.45,
        },
    )

    scored["overall_score"] = scored.apply(_overall_score_by_position, axis=1)
    scored["overall"] = scored["overall_score"]

    helper_columns = [column for column in scored.columns if column.startswith("_")]
    return scored.drop(columns=helper_columns)


def _overall_score_by_position(player):
    position_group = player.get("position_group")

    if position_group == "GK":
        score = (
            player["keeper_score"] * 0.55
            + player["stamina_score"] * 0.20
            + player["defense_score"] * 0.15
            + player["discipline_score"] * 0.10
        )
    elif position_group == "DF":
        score = (
            player["defense_score"] * 0.45
            + player["stamina_score"] * 0.25
            + player["discipline_score"] * 0.20
            + player["attack_score"] * 0.10
        )
    elif position_group == "MF":
        score = (
            player["stamina_score"] * 0.30
            + player["attack_score"] * 0.25
            + player["defense_score"] * 0.25
            + player["discipline_score"] * 0.20
        )
    else:
        score = (
            player["attack_score"] * 0.55
            + player["stamina_score"] * 0.25
            + player["discipline_score"] * 0.15
            + player["defense_score"] * 0.05
        )

    return round(max(0, min(100, score)), 2)


def load_manager_players(path=None):
    data_path = Path(path) if path else _first_existing_data_file()
    players = _read_data_file(data_path)
    players = select_manager_columns(players)
    return add_manager_scores(players)
