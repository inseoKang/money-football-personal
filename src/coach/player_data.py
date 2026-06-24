from pathlib import Path

import pandas as pd

from src.constants import RAW_DATA_DIR, SAMPLE_DATA_DIR
from src.coach.config import (
    BARCELONA_CLUB_ALIASES,
    BARCELONA_PLAYERS_FILE,
    LALIGA_KEYWORDS,
    MANAGER_PLAYERS_FILE,
)


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
    MANAGER_PLAYERS_FILE,
    MANAGER_PLAYERS_FILE.with_suffix(".xlsx"),
    RAW_DATA_DIR / "manager_players_ex.csv",
    RAW_DATA_DIR / "25-26_merged_manager_raw_data.xlsx",
]

COLUMN_ALIASES = {
    "player_name_clean": "player",
    "league_canonical": "league",
    "stats_club": "club",
    "stats_position": "position",
    "stats_age": "age",
    "stats_nation": "country",
    "salary_active": "active",
    "salary_loan": "loan",
}

DEFAULT_SEASON = "2025-2026"


def _first_existing_data_file():
    for path in DEFAULT_MANAGER_DATA_FILES:
        if path.exists():
            return path

    return SAMPLE_DATA_DIR / "sample_players.csv"


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


def _normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().casefold()


def _is_barcelona_club(value) -> bool:
    text = _normalize_text(value)
    return text in BARCELONA_CLUB_ALIASES or "barcelona" in text or "바르셀로나" in text


def _is_laliga_league(value) -> bool:
    text = _normalize_text(value)
    return any(keyword in text for keyword in LALIGA_KEYWORDS)

def _apply_column_aliases(players):
    output = players.copy()

    for source, target in COLUMN_ALIASES.items():
        if source in output.columns and target not in output.columns:
            output[target] = output[source]

    if "position_group" not in output.columns:
        if "position" in output.columns:
            output["position_group"] = output["position"]
        else:
            output["position_group"] = "UNK"

    if "season" not in output.columns:
        output["season"] = DEFAULT_SEASON

    if "salary_id" not in output.columns:
        output["salary_id"] = range(1, len(output) + 1)

    return output

def select_manager_columns(players):
    output = _apply_column_aliases(players)

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


def export_barcelona_players(force: bool = False) -> Path:
    """manager_players 전체 데이터에서 Barcelona 선수만 추출해 data/barcelona_players.csv를 생성합니다."""
    if BARCELONA_PLAYERS_FILE.exists() and not force:
        return BARCELONA_PLAYERS_FILE

    BARCELONA_PLAYERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    players = load_manager_players()
    barcelona = players[players["club"].map(_is_barcelona_club)].copy()
    barcelona.to_csv(BARCELONA_PLAYERS_FILE, index=False, encoding="utf-8-sig")
    return BARCELONA_PLAYERS_FILE


def load_barcelona_players(force_export: bool = False):
    """내 스쿼드/감독 대시보드 전용 Barcelona 선수 데이터 로더입니다."""
    path = export_barcelona_players(force=force_export)
    return load_manager_players(path)


def load_laliga_players(exclude_barcelona: bool = False):
    """VS 스쿼드 상대 팀 선택용 LaLiga 선수 데이터 로더입니다."""
    players = load_manager_players()
    laliga = players[players["league"].map(_is_laliga_league)].copy()

    if exclude_barcelona:
        laliga = laliga[~laliga["club"].map(_is_barcelona_club)].copy()

    return laliga.reset_index(drop=True)


def get_laliga_club_options(exclude_barcelona: bool = True) -> list[str]:
    players = load_laliga_players(exclude_barcelona=exclude_barcelona)
    clubs = sorted(
        str(club)
        for club in players["club"].dropna().unique()
        if str(club).strip()
    )
    return clubs
