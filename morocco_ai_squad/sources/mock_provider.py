from __future__ import annotations

import pandas as pd

from morocco_ai_squad.data_loader import load_seed_players
from morocco_ai_squad.sources.base import PlayerDataProvider


class MockProvider(PlayerDataProvider):
    name = "mock_seed"

    def fetch(self) -> pd.DataFrame:
        return load_seed_players()
