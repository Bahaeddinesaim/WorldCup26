from __future__ import annotations

import pandas as pd

from morocco_ai_squad.database.models import NA_VALUE


WEIGHTS = {
    "recent_form": 0.25,
    "league_level": 0.15,
    "playing_time_score": 0.20,
    "international_experience": 0.15,
    "tactical_fit": 0.15,
    "versatility": 0.10,
}


LEAGUE_LEVELS = {
    "Premier League": 95,
    "La Liga": 94,
    "Ligue 1": 86,
    "Bundesliga": 92,
    "Serie A": 91,
    "Eredivisie": 78,
    "Belgian Pro League": 72,
    "Saudi Pro League": 70,
    "Super League Greece": 68,
    "Botola Pro": 55,
}


def to_number(value) -> float | None:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return None
    return float(number)


def playing_time_score(minutes) -> float | None:
    value = to_number(minutes)
    if value is None:
        return None
    return round(min(value / 1800 * 100, 100), 1)


def recent_form_score(row: pd.Series) -> float | None:
    rating = to_number(row.get("avg_rating", NA_VALUE))
    if rating is not None:
        return round(min(max((rating - 5.5) / 2.5 * 100, 0), 100), 1)
    goals = to_number(row.get("goals", NA_VALUE))
    assists = to_number(row.get("assists", NA_VALUE))
    minutes = to_number(row.get("minutes_played", NA_VALUE))
    if goals is None or assists is None or minutes in (None, 0):
        return None
    return round(min(((goals + assists) / minutes) * 900 * 20, 100), 1)


def league_level_score(league) -> float | None:
    if league in (None, "", NA_VALUE):
        return None
    return float(LEAGUE_LEVELS.get(str(league), 60))


def reliability_bonus(reliability: str) -> float:
    return {"HIGH": 1.0, "MEDIUM": 0.85, "LOW": 0.65}.get(str(reliability), 0.5)


def add_real_data_scores(players: pd.DataFrame) -> pd.DataFrame:
    df = players.copy()
    df["recent_form"] = df.apply(lambda row: recent_form_score(row), axis=1)
    df["league_level"] = df["league"].apply(league_level_score) if "league" in df else None
    df["playing_time_score"] = df["minutes_played"].apply(playing_time_score) if "minutes_played" in df else None

    # These remain N/A until real international/tactical models are connected.
    for col in ["international_experience", "tactical_fit", "versatility"]:
        if col not in df.columns:
            df[col] = NA_VALUE

    scores = []
    explanations = []
    for _, row in df.iterrows():
        available = {k: to_number(row.get(k, NA_VALUE)) for k in WEIGHTS}
        available = {k: v for k, v in available.items() if v is not None}
        if len(available) < 3:
            scores.append(NA_VALUE)
            explanations.append(
                "Insufficient real data for a reliable score. Need at least form, league level and minutes."
            )
            continue
        weighted = sum(available[k] * WEIGHTS[k] for k in available)
        weight_sum = sum(WEIGHTS[k] for k in available)
        score = round((weighted / weight_sum) * reliability_bonus(row.get("reliability", "LOW")), 2)
        scores.append(score)
        explanations.append(
            "Computed only from available real fields: "
            + ", ".join(f"{k}={available[k]}" for k in available)
            + f". Reliability={row.get('reliability', 'LOW')}."
        )

    df["final_score"] = scores
    df["score_explanation"] = explanations
    return df
