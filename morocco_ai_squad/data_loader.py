from __future__ import annotations

import pandas as pd

from .config import PLAYERS_SEED_PATH
from .database.db import load_players
from .services.data_merger import load_cached_or_refresh, load_player_seed, refresh_real_data


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


def load_seed_players(path=PLAYERS_SEED_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, keep_default_na=False).replace("", "N/A")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def ensure_database_seeded() -> pd.DataFrame:
    db_df = load_players()
    if not db_df.empty:
        return db_df
    return load_cached_or_refresh()


def ensure_real_data_loaded() -> pd.DataFrame:
    return load_cached_or_refresh()


def refresh_real_pipeline() -> tuple[pd.DataFrame, pd.DataFrame]:
    return refresh_real_data()


def filter_players(df: pd.DataFrame, search: str, lines: list[str], source_types: list[str]) -> pd.DataFrame:
    filtered = df.copy()
    if search:
        text = search.lower().strip()
        filtered = filtered[
            filtered["player_name"].str.lower().str.contains(text)
            | filtered.get("club", pd.Series("", index=filtered.index)).astype(str).str.lower().str.contains(text)
            | filtered["primary_position"].str.lower().str.contains(text)
        ]
    if lines:
        filtered = filtered[filtered["line"].isin(lines)]
    if source_types:
        source_col = "reliability" if "reliability" in filtered.columns else "data_status"
        filtered = filtered[filtered[source_col].isin(source_types)]
    return filtered
