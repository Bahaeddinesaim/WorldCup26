from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class WhoScoredCollector(BaseCollector):
    name = "WhoScored"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        return self.skipped("WhoScored scraping is disabled by default; many pages require dynamic/session access.")
