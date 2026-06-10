from __future__ import annotations

from datetime import timedelta

import pandas as pd

from morocco_ai_squad.database.models import METRIC_COLUMNS, NA_VALUE


REQUIRED_IDENTITY = ["player_id", "player_name", "primary_position", "line"]
HIGH_VALUE_METRICS = ["club", "league", "matches_played", "minutes_played", "goals", "assists"]


def missing_value_report(players: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in REQUIRED_IDENTITY + HIGH_VALUE_METRICS + ["data_source", "last_updated", "reliability"]:
        if col not in players.columns:
            rows.append({"field": col, "missing_count": len(players), "missing_pct": 100.0, "severity": "HIGH"})
            continue
        missing = players[col].isna() | players[col].astype(str).isin(["", NA_VALUE, "nan"])
        pct = round(float(missing.mean() * 100), 1) if len(players) else 0
        severity = "HIGH" if col in REQUIRED_IDENTITY and missing.any() else "MEDIUM" if pct > 50 else "LOW"
        rows.append({"field": col, "missing_count": int(missing.sum()), "missing_pct": pct, "severity": severity})
    return pd.DataFrame(rows)


def stale_data_report(players: pd.DataFrame, max_age_days: int = 14) -> pd.DataFrame:
    if "last_updated" not in players.columns:
        return pd.DataFrame([{"player_name": "ALL", "issue": "Missing last_updated column", "severity": "HIGH"}])
    updated = pd.to_datetime(players["last_updated"], errors="coerce", utc=True)
    stale = updated.isna() | (pd.Timestamp.utcnow() - updated > timedelta(days=max_age_days))
    return players.loc[stale, ["player_name", "data_source", "last_updated", "reliability"]].assign(
        issue=f"Older than {max_age_days} days or invalid timestamp",
        severity="MEDIUM",
    )


def incoherence_report(players: pd.DataFrame) -> pd.DataFrame:
    issues = []
    numeric_fields = ["age", "matches_played", "minutes_played", "goals", "assists", "clean_sheets", "xg", "xa"]
    for _, row in players.iterrows():
        for field in numeric_fields:
            if field not in players.columns:
                continue
            value = row.get(field)
            if value in (NA_VALUE, "", None):
                continue
            number = pd.to_numeric(value, errors="coerce")
            if pd.isna(number):
                issues.append({"player_name": row["player_name"], "field": field, "value": value, "issue": "Not numeric"})
            elif number < 0:
                issues.append({"player_name": row["player_name"], "field": field, "value": value, "issue": "Negative value"})
        minutes = pd.to_numeric(row.get("minutes_played", NA_VALUE), errors="coerce")
        matches = pd.to_numeric(row.get("matches_played", NA_VALUE), errors="coerce")
        if not pd.isna(minutes) and not pd.isna(matches) and matches > 0 and minutes > matches * 130:
            issues.append(
                {
                    "player_name": row["player_name"],
                    "field": "minutes_played",
                    "value": minutes,
                    "issue": "Minutes exceed plausible match total",
                }
            )
    return pd.DataFrame(issues)


def quality_summary(players: pd.DataFrame) -> dict:
    metrics_present = 0
    total_metrics = len(players) * len(METRIC_COLUMNS)
    for col in METRIC_COLUMNS:
        if col in players.columns:
            metrics_present += (~players[col].astype(str).isin([NA_VALUE, "", "nan"])).sum()
    completeness = round(float(metrics_present / total_metrics * 100), 1) if total_metrics else 0
    real_rows = int((players.get("collection_status", pd.Series(dtype=str)) == "REAL").sum())
    return {
        "players": len(players),
        "metric_completeness_pct": completeness,
        "real_data_rows": real_rows,
        "seed_only_rows": int((players.get("collection_status", pd.Series(dtype=str)) == "SEED_ONLY").sum()),
    }
