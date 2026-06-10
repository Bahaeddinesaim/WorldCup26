from __future__ import annotations

import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult, utc_now


class FBrefCollector(BaseCollector):
    name = "FBref"
    reliability = "HIGH"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        rows: list[dict] = []
        logs: list[dict] = []
        configured = seed[seed["fbref_url"].fillna("N/A") != "N/A"]
        if configured.empty:
            return CollectorResult(
                self.name,
                pd.DataFrame(),
                pd.DataFrame([self.log("NOT_CONFIGURED", "No fbref_url configured in data/players_seed.csv.")]),
            )

        for player in configured.to_dict("records"):
            url = player["fbref_url"]
            try:
                tables = pd.read_html(url)
                if not tables:
                    logs.append(self.log("EMPTY", f"No HTML tables found for {player['player_name']}", url))
                    continue
                merged = self._extract_basic_metrics(player["player_id"], tables, url)
                rows.append(merged)
                logs.append(self.log("OK", f"Collected FBref tables for {player['player_name']}", url))
            except Exception as exc:
                logs.append(self.log("FAILED", f"{player['player_name']}: {exc}", url))

        return CollectorResult(self.name, pd.DataFrame(rows), pd.DataFrame(logs))

    def _extract_basic_metrics(self, player_id: str, tables: list[pd.DataFrame], source_url: str) -> dict:
        # FBref table structure changes by page and competition. This extractor
        # takes only clear season summary columns when present and leaves the rest N/A.
        best = tables[0].copy()
        if isinstance(best.columns, pd.MultiIndex):
            best.columns = ["_".join([str(p) for p in col if str(p) != "nan"]).strip("_") for col in best.columns]
        row = best.tail(1).to_dict("records")[0] if not best.empty else {}

        def pick(*names: str):
            lowered = {str(k).lower(): k for k in row.keys()}
            for name in names:
                if name.lower() in lowered:
                    return row[lowered[name.lower()]]
            return "N/A"

        return {
            "player_id": player_id,
            "matches_played": pick("MP", "Playing Time_MP"),
            "minutes_played": pick("Min", "Playing Time_Min"),
            "goals": pick("Gls", "Performance_Gls"),
            "assists": pick("Ast", "Performance_Ast"),
            "xg": pick("xG", "Expected_xG"),
            "xa": pick("xAG", "Expected_xAG", "xA"),
            "data_source": self.name,
            "source_url": source_url,
            "last_updated": utc_now(),
            "reliability": self.reliability,
            "collection_status": "REAL",
            "collection_notes": "Parsed configured FBref public page tables.",
        }
