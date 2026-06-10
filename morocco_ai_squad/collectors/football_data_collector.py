from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class FootballDataCollector(BaseCollector):
    name = "Football-Data.co.uk"
    reliability = "HIGH"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        return self.skipped(
            "Football-Data.co.uk mainly provides match/team CSVs, not player-level squad statistics."
        )
