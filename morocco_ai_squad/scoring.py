from __future__ import annotations

import pandas as pd


WEIGHTS = {
    "recent_form": 0.25,
    "league_level": 0.15,
    "playing_time_score": 0.20,
    "international_experience": 0.15,
    "tactical_fit": 0.15,
    "versatility": 0.10,
}


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
    return round(sum(float(row[k]) * weight for k, weight in WEIGHTS.items()), 2)


def add_scores(players: pd.DataFrame) -> pd.DataFrame:
    df = players.copy()
    df["final_score"] = df.apply(compute_score, axis=1)
    df["score_explanation"] = df.apply(explain_score, axis=1)
    return df.sort_values("final_score", ascending=False).reset_index(drop=True)


def explain_score(row: pd.Series) -> str:
    pieces = [
        f"Forme recente {row['recent_form']}/100 ponderee a 25%",
        f"niveau championnat {row['league_level']}/100 a 15%",
        f"temps de jeu {row['playing_time_score']}/100 a 20%",
        f"experience internationale {row['international_experience']}/100 a 15%",
        f"fit tactique {row['tactical_fit']}/100 a 15%",
        f"polyvalence {row['versatility']}/100 a 10%",
    ]
    return "; ".join(pieces) + f". Score final: {compute_score(row)}/100."


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
