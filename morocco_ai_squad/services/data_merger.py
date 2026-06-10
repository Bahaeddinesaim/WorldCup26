from __future__ import annotations

from datetime import timedelta

import pandas as pd

from morocco_ai_squad.collectors.api_football_collector import ApiFootballCollector
from morocco_ai_squad.collectors.fbref_collector import FBrefCollector
from morocco_ai_squad.collectors.football_data_collector import FootballDataCollector
from morocco_ai_squad.collectors.fotmob_collector import FotMobCollector
from morocco_ai_squad.collectors.sofascore_collector import SofascoreCollector
from morocco_ai_squad.collectors.statsbomb_open_data_collector import StatsBombOpenDataCollector
from morocco_ai_squad.collectors.transfermarkt_collector import TransfermarktCollector
from morocco_ai_squad.collectors.understat_collector import UnderstatCollector
from morocco_ai_squad.collectors.whoscored_collector import WhoScoredCollector
from morocco_ai_squad.collectors.base import utc_now
from morocco_ai_squad.config import PLAYERS_SEED_PATH
from morocco_ai_squad.database.db import load_players, save_fetch_logs, save_players
from morocco_ai_squad.database.models import METRIC_COLUMNS, NA_VALUE, PLAYER_COLUMNS, PROVENANCE_COLUMNS
from morocco_ai_squad.services.player_scoring import add_real_data_scores


COLLECTORS = [
    ApiFootballCollector(),
    FBrefCollector(),
    SofascoreCollector(),
    FotMobCollector(),
    TransfermarktCollector(),
    WhoScoredCollector(),
    UnderstatCollector(),
    StatsBombOpenDataCollector(),
    FootballDataCollector(),
]


def load_player_seed(path=PLAYERS_SEED_PATH) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False).replace("", NA_VALUE)


def empty_player_frame(seed: pd.DataFrame) -> pd.DataFrame:
    df = seed[["player_id", "player_name", "short_name", "line", "primary_position", "secondary_positions", "country"]].copy()
    for col in METRIC_COLUMNS:
        df[col] = NA_VALUE
    for col in PROVENANCE_COLUMNS:
        df[col] = NA_VALUE
    df["data_source"] = "Manual seed"
    df["source_url"] = PLAYERS_SEED_PATH.name
    df["last_updated"] = utc_now()
    df["reliability"] = "LOW"
    df["collection_status"] = "SEED_ONLY"
    df["collection_notes"] = "Identity/position seed only; no performance metrics collected yet."
    return df


def merge_provider_rows(base: pd.DataFrame, provider_rows: pd.DataFrame) -> pd.DataFrame:
    if provider_rows.empty:
        return base

    merged = base.copy()
    provider_rows = provider_rows.replace("", NA_VALUE).fillna(NA_VALUE)
    for row in provider_rows.to_dict("records"):
        player_id = row.get("player_id")
        if player_id not in set(merged["player_id"]):
            continue
        idx = merged.index[merged["player_id"] == player_id][0]
        sources = set(str(merged.at[idx, "data_source"]).split(" | ")) - {NA_VALUE}
        for col, value in row.items():
            if col == "player_id" or value in (None, "", NA_VALUE):
                continue
            if col in merged.columns:
                merged.at[idx, col] = value
        if row.get("data_source") not in (None, "", NA_VALUE):
            sources.add(str(row["data_source"]))
            merged.at[idx, "data_source"] = " | ".join(sorted(sources))
    return merged


def refresh_real_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    seed = load_player_seed()
    players = empty_player_frame(seed)
    all_logs = []

    for collector in COLLECTORS:
        result = collector.fetch(seed)
        players = merge_provider_rows(players, result.rows)
        all_logs.append(result.logs)

    logs = pd.concat(all_logs, ignore_index=True) if all_logs else pd.DataFrame()
    players = add_real_data_scores(players)
    players = players.reindex(columns=[col for col in PLAYER_COLUMNS if col in players.columns])
    save_players(players)
    save_fetch_logs(logs)
    return players, logs


def load_cached_or_refresh(max_age_hours: int = 24) -> pd.DataFrame:
    cached = load_players()
    if cached.empty:
        players, _ = refresh_real_data()
        return players
    if "last_updated" not in cached.columns:
        players, _ = refresh_real_data()
        return players
    latest = pd.to_datetime(cached["last_updated"], errors="coerce", utc=True).max()
    if pd.isna(latest) or pd.Timestamp.utcnow() - latest > timedelta(hours=max_age_hours):
        return cached
    return cached
