from __future__ import annotations

import pandas as pd

from .config import PLAYERS_SEED_PATH
from .database.db import load_players
from .services.data_merger import load_cached_or_refresh, load_player_seed, refresh_real_data

NA_VALUE = "N/A"

REQUIRED_DEFAULTS = {
    "player_id": NA_VALUE,
    "player_name": NA_VALUE,
    "short_name": NA_VALUE,
    "line": NA_VALUE,
    "primary_position": NA_VALUE,
    "secondary_positions": NA_VALUE,
    "role_projection": NA_VALUE,
    "final_score": NA_VALUE,
    "score_explanation": NA_VALUE,
    "club": NA_VALUE,
    "league": NA_VALUE,
    "age": NA_VALUE,
    "minutes": 0,
    "minutes_played": NA_VALUE,
    "matches_played": NA_VALUE,
    "goals": 0,
    "assists": 0,
    "clean_sheets": NA_VALUE,
    "xg": NA_VALUE,
    "xa": NA_VALUE,
    "avg_rating": NA_VALUE,
    "data_source": NA_VALUE,
    "source_url": NA_VALUE,
    "last_updated": NA_VALUE,
    "reliability": "LOW",
    "collection_status": NA_VALUE,
    "collection_notes": NA_VALUE,
    "injury_status": NA_VALUE,
    "recent_form": NA_VALUE,
    "league_level": NA_VALUE,
    "playing_time_score": NA_VALUE,
    "international_experience": NA_VALUE,
    "tactical_fit": NA_VALUE,
    "versatility": NA_VALUE,
    "position_group": NA_VALUE,
}


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
    return ensure_required_columns(df)


def safe_get(row, column: str, default=NA_VALUE):
    """Return a cell-like value without raising on missing columns/keys."""
    try:
        if isinstance(row, pd.Series):
            value = row[column] if column in row.index else default
        elif isinstance(row, dict):
            value = row.get(column, default)
        else:
            value = getattr(row, column, default)
    except Exception:
        return default

    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    if isinstance(value, str) and value.strip() == "":
        return default
    return value


def ensure_required_columns(df: pd.DataFrame | None) -> pd.DataFrame:
    """Guarantee a minimum app schema for partial CSV/API/cache data."""
    if df is None or df.empty:
        df = pd.DataFrame(columns=REQUIRED_DEFAULTS.keys())
    else:
        df = df.copy()

    for column, default in REQUIRED_DEFAULTS.items():
        if column not in df.columns:
            df[column] = default
        else:
            df[column] = df[column].where(~df[column].isna(), default)
            if default == NA_VALUE:
                df[column] = df[column].replace("", default)

    if "minutes" in df.columns and "minutes_played" in df.columns:
        missing_minutes = df["minutes"].astype(str).isin(["", NA_VALUE, "nan", "None"])
        df.loc[missing_minutes, "minutes"] = pd.to_numeric(df["minutes_played"], errors="coerce").fillna(0)

    missing_short = df["short_name"].astype(str).isin(["", NA_VALUE, "nan", "None"])
    df.loc[missing_short, "short_name"] = df.loc[missing_short, "player_name"]

    missing_role = df["role_projection"].astype(str).isin(["", NA_VALUE, "nan", "None"])
    df.loc[missing_role, "role_projection"] = df.loc[missing_role, "primary_position"].apply(
        lambda value: f"Squad option ({value})" if value not in ("", NA_VALUE, None) else NA_VALUE
    )

    return df


def ensure_database_seeded() -> pd.DataFrame:
    db_df = load_players()
    if not db_df.empty:
        return ensure_required_columns(db_df)
    return ensure_required_columns(load_cached_or_refresh())


def ensure_real_data_loaded() -> pd.DataFrame:
    return ensure_required_columns(load_cached_or_refresh())


def refresh_real_pipeline() -> tuple[pd.DataFrame, pd.DataFrame]:
    players, logs = refresh_real_data()
    return ensure_required_columns(players), logs


def filter_players(df: pd.DataFrame, search: str, lines: list[str], source_types: list[str]) -> pd.DataFrame:
    filtered = ensure_required_columns(df)
    if search:
        text = search.lower().strip()
        filtered = filtered[
            filtered["player_name"].str.lower().str.contains(text)
            | filtered.get("club", pd.Series("", index=filtered.index)).astype(str).str.lower().str.contains(text)
            | filtered.get("primary_position", pd.Series("", index=filtered.index)).astype(str).str.lower().str.contains(text)
        ]
    if lines:
        filtered = filtered[filtered["line"].isin(lines)]
    if source_types:
        source_col = "reliability" if "reliability" in filtered.columns else "data_status"
        filtered = filtered[filtered[source_col].isin(source_types)]
    return filtered
