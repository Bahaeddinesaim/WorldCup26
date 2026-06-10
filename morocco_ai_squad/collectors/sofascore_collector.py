from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class SofascoreCollector(BaseCollector):
    name = "Sofascore"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        configured = seed[seed["sofascore_id"].fillna("N/A") != "N/A"]
        if configured.empty:
            return self.skipped("No sofascore_id configured. Add IDs only if automated access is allowed.")
        return self.skipped(
            "Sofascore public endpoints are not enabled by default. Implement only with permitted API access."
        )
