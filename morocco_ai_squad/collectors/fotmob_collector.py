from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class FotMobCollector(BaseCollector):
    name = "FotMob"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        seed = seed.copy()
        if "fotmob_id" not in seed.columns:
            seed["fotmob_id"] = "N/A"
        if "fotmob_url" not in seed.columns:
            seed["fotmob_url"] = "N/A"
        configured = seed[seed["fotmob_id"].fillna("N/A") != "N/A"]
        if configured.empty:
            logs = [
                self.log("NOT_CONFIGURED", f"[INFO] {row['player_name']} Source: FotMob missing fotmob_id/fotmob_url", row.get("fotmob_url", "N/A"), row["player_name"], 0)
                for row in seed.to_dict("records")
            ]
            return CollectorResult(self.name, pd.DataFrame(), pd.DataFrame(logs))
        return CollectorResult(
            self.name,
            pd.DataFrame(),
            pd.DataFrame([self.log("NOT_CONFIGURED", "FotMob parser not enabled for configured IDs yet.")]),
        )
