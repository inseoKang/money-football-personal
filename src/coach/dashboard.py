from src.coach.scoring import safe_number


def _get_name_column(players_df):
    if "name" in players_df.columns:
        return "name"
    if "Player" in players_df.columns:
        return "Player"
    if "player" in players_df.columns:
        return "player"
    return None


def _get_first_existing_column(players_df, candidates):
    for column in candidates:
        if column in players_df.columns:
            return column
    return None


def get_dashboard_summary(players_df):
    name_column = _get_name_column(players_df)

    overall_column = _get_first_existing_column(
        players_df,
        ["overall_score", "overall"],
    )

    market_value_column = _get_first_existing_column(
        players_df,
        [
            "tm_current_market_value_eur",
            "tm_market_value_season_eur",
            "market_value_eur",
            "annual_gross_eur",
        ],
    )

    player_count = len(players_df)

    if overall_column:
        avg_overall = float(round(players_df[overall_column].fillna(0).mean(), 2))
        top_player_row = players_df.sort_values(
            overall_column,
            ascending=False,
        ).iloc[0]
    else:
        avg_overall = 0.0
        top_player_row = players_df.iloc[0] if player_count > 0 else None

    if market_value_column:
        avg_market_value = float(round(players_df[market_value_column].fillna(0).mean(), 2))
    else:
        avg_market_value = 0.0

    if top_player_row is not None and name_column:
        top_player = top_player_row[name_column]
    else:
        top_player = None

    return {
        "player_count": player_count,
        "avg_overall": avg_overall,
        "avg_market_value": avg_market_value,
        "top_player": top_player,
    }


def sort_players(players_df, sort_key):
    sort_options = {
        "종합 점수 높은 순": ["overall_score", "overall"],
        "시장가치 높은 순": [
            "tm_current_market_value_eur",
            "tm_market_value_season_eur",
            "market_value_eur",
            "annual_gross_eur",
        ],
        "공격 점수 높은 순": ["attack_score", "shooting", "goals"],
        "수비 점수 높은 순": ["defense_score", "defending", "tackles"],
        "나이 어린 순": ["age", "Age"],
        "가성비 높은 순": ["value_score"],
    }

    candidate_columns = sort_options.get(sort_key)

    if not candidate_columns:
        return players_df

    sort_column = _get_first_existing_column(players_df, candidate_columns)

    if sort_column is None:
        return players_df

    ascending = sort_key == "나이 어린 순"

    return players_df.sort_values(
        sort_column,
        ascending=ascending,
    )