from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
STYLE_DIR = ROOT_DIR / "styles"
PROMPT_DIR = ROOT_DIR / "prompts"

PROCESSED_DATA_DIR = DATA_DIR / "processed"
RAW_DATA_DIR = DATA_DIR / "raw"
SAMPLE_DATA_DIR = DATA_DIR / "sample"

# 공통/감독 데이터
PLAYERS_CSV_PATH = PROCESSED_DATA_DIR / "barcelona_players.csv"
MANAGER_PLAYERS_CSV_PATH = PROCESSED_DATA_DIR / "manager_players.csv"
BARCELONA_PLAYERS_CSV_PATH = PROCESSED_DATA_DIR / "barcelona_players.csv"

# 스카우터 데이터
SCOUT_PLAYERS_CSV_PATH = PROCESSED_DATA_DIR / "scout_player_view_2526.csv"

# 샘플 데이터
SAMPLE_PLAYERS_CSV_PATH = SAMPLE_DATA_DIR / "sample_players.csv"

DEFAULT_FORMATION = "4-3-3"

COACH_PAGES = {
    "내 스쿼드": "coach_squad",
    "VS 스쿼드": "coach_vs_squad",
    "선수 대시보드": "coach_dashboard",
}

SCOUT_PAGES = {
    "스카우팅 검색": "scout_search",
    "스카우팅 결과": "scout_result",
    "전체 선수 시장 대시보드": "scout_market_dashboard",
}

POSITION_GROUPS = ["전체", "GK", "DF", "MF", "FW"]

NUMERIC_COLUMNS = [
    "number",
    "height",
    "overall",
    "attack_score",
    "midfield_score",
    "defense_score",
    "pace_score",
    "physical_score",
    "stamina_score",
    "gk_score",
    "market_value",
    "wage",
    "age",
]