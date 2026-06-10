from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .config import SQLITE_PATH


PLAYER_TABLE = "players"


def get_connection(db_path: Path = SQLITE_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def initialize_database(players: pd.DataFrame, db_path: Path = SQLITE_PATH) -> None:
    with get_connection(db_path) as conn:
        players.to_sql(PLAYER_TABLE, conn, if_exists="replace", index=False)


def load_players_from_db(db_path: Path = SQLITE_PATH) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame()
    with get_connection(db_path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {PLAYER_TABLE}", conn)
