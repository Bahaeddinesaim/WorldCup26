from __future__ import annotations

PLAYER_TABLE = "real_player_metrics"
FETCH_LOG_TABLE = "data_fetch_logs"

RELIABILITY_HIGH = "HIGH"
RELIABILITY_MEDIUM = "MEDIUM"
RELIABILITY_LOW = "LOW"

NA_VALUE = "N/A"

IDENTITY_COLUMNS = [
    "player_id",
    "player_name",
    "short_name",
    "line",
    "primary_position",
    "secondary_positions",
    "country",
]

METRIC_COLUMNS = [
    "age",
    "club",
    "league",
    "player_status",
    "player_image",
    "matches_played",
    "minutes_played",
    "goals",
    "assists",
    "clean_sheets",
    "xg",
    "xa",
    "avg_rating",
    "market_value",
    "injury_status",
    "transfer_history",
    "defensive_actions",
    "offensive_actions",
    "form_recent",
]

PROVENANCE_COLUMNS = [
    "data_source",
    "source_url",
    "last_updated",
    "reliability",
    "collection_status",
    "collection_notes",
]

SCORING_COLUMNS = [
    "recent_form",
    "league_level",
    "playing_time_score",
    "international_experience",
    "tactical_fit",
    "versatility",
    "final_score",
    "score_explanation",
]

PLAYER_COLUMNS = IDENTITY_COLUMNS + METRIC_COLUMNS + PROVENANCE_COLUMNS + SCORING_COLUMNS

FETCH_LOG_COLUMNS = [
    "collector",
    "player_name",
    "status",
    "message",
    "source_url",
    "fields_updated",
    "last_updated",
]
