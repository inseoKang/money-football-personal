"""Build the processed 25/26 scout player view."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scout.scout_features import DEFAULT_BASE_PATH, DEFAULT_VIEW_PATH, build_and_save_scout_player_view


def main() -> None:
    parser = argparse.ArgumentParser(description="Build data/processed/scout_player_view_2526.csv")
    parser.add_argument("--input", default=str(DEFAULT_BASE_PATH), help="Source scout player base CSV")
    parser.add_argument("--output", default=str(DEFAULT_VIEW_PATH), help="Processed scout player view CSV")
    args = parser.parse_args()

    rows = build_and_save_scout_player_view(Path(args.input), Path(args.output))
    print(f"input: {args.input}")
    print(f"output: {args.output}")
    print(f"rows: {len(rows)}")


if __name__ == "__main__":
    main()
