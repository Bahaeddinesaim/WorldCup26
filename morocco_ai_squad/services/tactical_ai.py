from __future__ import annotations

import pandas as pd

from morocco_ai_squad.tactics import build_lineup, recommended_formation


def build_real_data_lineup(players: pd.DataFrame, formation: str) -> dict:
    return build_lineup(players, formation)


def recommend_real_data_formation(players: pd.DataFrame) -> str:
    return recommended_formation(players)
