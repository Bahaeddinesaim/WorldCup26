from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class WhoScoredCollector(BaseCollector):
    name = "WhoScored"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        logs = [
            self.log("NOT_CONFIGURED", f"[INFO] {row['player_name']} Source: WhoScored missing whoscored_url", row.get("whoscored_url", "N/A"), row["player_name"], 0)
            for row in seed.to_dict("records")
        ]
        return CollectorResult(self.name, pd.DataFrame(), pd.DataFrame(logs))
