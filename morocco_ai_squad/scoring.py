from __future__ import annotations

import pandas as pd

from morocco_ai_squad.database.models import NA_VALUE
from morocco_ai_squad.services.player_scoring import WEIGHTS, add_real_data_scores


POSITION_GROUPS = {
    "Goalkeepers": ["GK"],
    "Centre backs": ["CB"],
    "Full backs": ["RB", "LB", "RWB", "LWB"],
    "Defensive midfielders": ["DM", "CM"],
    "Creative midfielders": ["AM", "CM"],
    "Wingers": ["RW", "LW"],
    "Strikers": ["ST", "CF"],
}


def compute_score(row: pd.Series) -> float:
    scored = add_real_data_scores(pd.DataFrame([row]))
    value = scored.iloc[0]["final_score"]
    return value if value != NA_VALUE else NA_VALUE


def add_scores(players: pd.DataFrame) -> pd.DataFrame:
    df = add_real_data_scores(players)
    sort_key = pd.to_numeric(df["final_score"], errors="coerce").fillna(-1)
    return df.assign(_sort_key=sort_key).sort_values("_sort_key", ascending=False).drop(columns="_sort_key").reset_index(drop=True)


def explain_score(row: pd.Series) -> str:
    return str(row.get("score_explanation", "Insufficient real data for scoring."))


def position_group_for_player(row: pd.Series) -> str:
    positions = {row["primary_position"], *str(row["secondary_positions"]).split("|")}
    for group, aliases in POSITION_GROUPS.items():
        if positions.intersection(aliases):
            return group
    return row["line"]


def add_position_groups(players: pd.DataFrame) -> pd.DataFrame:
    df = players.copy()
    df["position_group"] = df.apply(position_group_for_player, axis=1)
    return df


def compare_by_group(players: pd.DataFrame, group: str) -> pd.DataFrame:
    aliases = POSITION_GROUPS.get(group, [])
    mask = players.apply(
        lambda row: bool({row["primary_position"], *str(row["secondary_positions"]).split("|")}.intersection(aliases)),
        axis=1,
    )
    return players[mask].sort_values("final_score", ascending=False)
