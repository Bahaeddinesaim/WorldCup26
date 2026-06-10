from __future__ import annotations

import pandas as pd
import requests

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult, utc_now


class SofascoreCollector(BaseCollector):
    name = "SofaScore"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        configured = seed[seed["sofascore_id"].fillna("N/A") != "N/A"]
        if configured.empty:
            return CollectorResult(
                self.name,
                pd.DataFrame(),
                pd.DataFrame([self.log("FAILED", "No sofascore_id configured.")]),
            )

        rows: list[dict] = []
        logs: list[dict] = []
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json,text/plain,*/*",
                "Referer": "https://www.sofascore.com/",
            }
        )

        for player in configured.to_dict("records"):
            player_name = player["player_name"]
            source_url = player.get("sofascore_url", "N/A")
            api_url = f"https://www.sofascore.com/api/v1/player/{player['sofascore_id']}"
            try:
                response = session.get(api_url, timeout=20)
                response.raise_for_status()
                payload = response.json().get("player", {})
                row = self._normalize(player, payload, source_url or api_url)
                fields_updated = sum(1 for key, value in row.items() if key != "player_id" and value not in ("N/A", "", None))
                rows.append(row)
                logs.append(self.log("SUCCESS", f"[INFO] {player_name} Source: SofaScore", source_url, player_name, fields_updated))
            except Exception as exc:
                logs.append(
                    self.log(
                        "FAILED",
                        f"[INFO] {player_name} Source: SofaScore Status: FAILED Detail: {exc}",
                        source_url,
                        player_name,
                        0,
                    )
                )

        return CollectorResult(self.name, pd.DataFrame(rows), pd.DataFrame(logs))

    def _normalize(self, seed_player: dict, payload: dict, source_url: str) -> dict:
        team = payload.get("team") or {}
        country = payload.get("country") or {}
        date_of_birth = payload.get("dateOfBirthTimestamp")
        age = "N/A"
        if date_of_birth:
            age = int((pd.Timestamp.utcnow().timestamp() - int(date_of_birth)) / (365.25 * 24 * 3600))

        return {
            "player_id": seed_player["player_id"],
            "player_name": payload.get("name", seed_player["player_name"]),
            "short_name": payload.get("shortName", seed_player.get("short_name", "N/A")),
            "age": age,
            "club": team.get("name", "N/A"),
            "league": "N/A",
            "primary_position": payload.get("position", seed_player.get("primary_position", "N/A")),
            "market_value": payload.get("proposedMarketValueRaw", {}).get("value", "N/A")
            if isinstance(payload.get("proposedMarketValueRaw"), dict)
            else payload.get("marketValue", "N/A"),
            "data_source": self.name,
            "source_url": source_url,
            "last_updated": utc_now(),
            "reliability": self.reliability,
            "collection_status": "REAL",
            "collection_notes": "Collected from SofaScore player endpoint.",
        }
