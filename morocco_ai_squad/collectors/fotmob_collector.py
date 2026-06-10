from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class FotMobCollector(BaseCollector):
    name = "FotMob"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        configured = seed[seed["fotmob_id"].fillna("N/A") != "N/A"]
        if configured.empty:
            return self.skipped("No fotmob_id configured. Add IDs only if collection is allowed.")
        return self.skipped("FotMob collector is scaffolded; enable only with compliant access.")
