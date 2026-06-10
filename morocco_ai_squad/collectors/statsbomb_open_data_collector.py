from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class StatsBombOpenDataCollector(BaseCollector):
    name = "StatsBomb Open Data"
    reliability = "HIGH"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        return self.skipped(
            "StatsBomb Open Data is match-event data, not universal season player data. "
            "Configure competition/match IDs before extracting player events."
        )
