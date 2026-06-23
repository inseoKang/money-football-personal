from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

PLAYERS_FILE = BASE_DIR / "data" / "sample_players.csv"
MANAGER_PLAYERS_FILE = BASE_DIR / "data" / "manager_players.csv"

COLUMN_MAP = {
    "player_id": "salary_id",
    "name": "player",
    "position": "position_group",
    "overall": "overall_score",
    "pace": "stamina_score",
    "shooting": "attack_score",
    "passing": "attack_score",
    "defending": "defense_score",
    "physical": "stamina_score",
}

TACTIC_WEIGHTS = {
    "balanced": {
        "overall": 0.5,
        "pace": 0.1,
        "shooting": 0.1,
        "passing": 0.1,
        "defending": 0.1,
        "physical": 0.1,
    },
    "attacking": {
        "overall": 0.35,
        "pace": 0.15,
        "shooting": 0.25,
        "passing": 0.15,
        "defending": 0.03,
        "physical": 0.07,
    },
    "defensive": {
        "overall": 0.35,
        "pace": 0.07,
        "shooting": 0.03,
        "passing": 0.1,
        "defending": 0.3,
        "physical": 0.15,
    },
}
