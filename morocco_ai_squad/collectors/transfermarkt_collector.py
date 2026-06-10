from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class TransfermarktCollector(BaseCollector):
    name = "Transfermarkt"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        configured = seed[seed["transfermarkt_url"].fillna("N/A") != "N/A"]
        if configured.empty:
            return self.skipped("No transfermarkt_url configured in data/players_seed.csv.")
        return self.skipped(
            "Transfermarkt automated scraping is disabled by default. Use an allowed API/export or manual CSV import."
        )
