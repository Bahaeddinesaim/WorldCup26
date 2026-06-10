from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult


class StatsBombOpenDataCollector(BaseCollector):
    name = "StatsBomb Open Data"
    reliability = "HIGH"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        return CollectorResult(
            self.name,
            pd.DataFrame(),
            pd.DataFrame(
                [
                    self.log(
                        "NOT_CONFIGURED",
                        "StatsBomb Open Data needs competition/match IDs before extracting player events.",
                    )
                ]
            ),
        )
