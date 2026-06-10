from __future__ import annotations

import pandas as pd

from .config import SEED_PLAYERS_PATH
from .database import initialize_database, load_players_from_db


NUMERIC_COLUMNS = [
    "age",
    "minutes_recent",
    "goals_recent",
    "assists_recent",
    "clean_sheets_recent",
    "duels_won_pct",
    "pass_success_pct",
    "avg_rating",
    "recent_form",
    "league_level",
    "playing_time_score",
    "international_experience",
    "tactical_fit",
    "versatility",
]


def load_seed_players(path=SEED_PLAYERS_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def ensure_database_seeded() -> pd.DataFrame:
    db_df = load_players_from_db()
    if not db_df.empty:
        return db_df
    players = load_seed_players()
    initialize_database(players)
    return players


def filter_players(df: pd.DataFrame, search: str, lines: list[str], source_types: list[str]) -> pd.DataFrame:
    filtered = df.copy()
    if search:
        text = search.lower().strip()
        filtered = filtered[
            filtered["player_name"].str.lower().str.contains(text)
            | filtered["club"].str.lower().str.contains(text)
            | filtered["primary_position"].str.lower().str.contains(text)
        ]
    if lines:
        filtered = filtered[filtered["line"].isin(lines)]
    if source_types:
        filtered = filtered[filtered["data_status"].isin(source_types)]
    return filtered
