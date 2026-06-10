from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class UnderstatCollector(BaseCollector):
    name = "Understat"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        configured = seed[seed["understat_id"].fillna("N/A") != "N/A"]
        if configured.empty:
            return self.skipped("No understat_id configured. Understat coverage is league-limited.")
        return self.skipped("Understat collector scaffolded; add permitted endpoint handling before enabling.")
