from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class UnderstatCollector(BaseCollector):
    name = "Understat"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        configured = seed[seed["understat_id"].fillna("N/A") != "N/A"]
        if configured.empty:
            return CollectorResult(
                self.name,
                pd.DataFrame(),
                pd.DataFrame([self.log("NOT_CONFIGURED", "No understat_id configured. Understat coverage is league-limited.")]),
            )
        return CollectorResult(
            self.name,
            pd.DataFrame(),
            pd.DataFrame([self.log("NOT_CONFIGURED", "Understat parser not enabled for configured IDs yet.")]),
        )
