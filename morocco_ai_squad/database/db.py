from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from morocco_ai_squad.config import SQLITE_PATH
from morocco_ai_squad.database.models import FETCH_LOG_TABLE, PLAYER_TABLE


def get_connection(db_path: Path = SQLITE_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def initialize_database(db_path: Path = SQLITE_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {PLAYER_TABLE} (
                player_id TEXT PRIMARY KEY,
                player_name TEXT,
                payload TEXT
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {FETCH_LOG_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collector TEXT,
                status TEXT,
                message TEXT,
                source_url TEXT,
                last_updated TEXT
            )
            """
        )


def save_players(players: pd.DataFrame, db_path: Path = SQLITE_PATH) -> None:
    initialize_database(db_path)
    with get_connection(db_path) as conn:
        players.to_sql(PLAYER_TABLE, conn, if_exists="replace", index=False)


def load_players(db_path: Path = SQLITE_PATH) -> pd.DataFrame:
    initialize_database(db_path)
    with get_connection(db_path) as conn:
        try:
            return pd.read_sql_query(f"SELECT * FROM {PLAYER_TABLE}", conn)
        except Exception:
            return pd.DataFrame()


def save_fetch_logs(logs: pd.DataFrame, db_path: Path = SQLITE_PATH) -> None:
    initialize_database(db_path)
    if logs.empty:
        return
    with get_connection(db_path) as conn:
        logs.to_sql(FETCH_LOG_TABLE, conn, if_exists="append", index=False)


def load_fetch_logs(db_path: Path = SQLITE_PATH) -> pd.DataFrame:
    initialize_database(db_path)
    with get_connection(db_path) as conn:
        try:
            return pd.read_sql_query(
                f"SELECT * FROM {FETCH_LOG_TABLE} ORDER BY id DESC LIMIT 200",
                conn,
            )
        except Exception:
            return pd.DataFrame()
