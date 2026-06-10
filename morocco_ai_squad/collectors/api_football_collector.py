from __future__ import annotations

import requests
import pandas as pd

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult, utc_now
from morocco_ai_squad.config import load_settings


class ApiFootballCollector(BaseCollector):
    name = "API-Football"
    reliability = "HIGH"

    def fetch(self, seed: pd.DataFrame, season: int = 2025) -> CollectorResult:
        settings = load_settings()
        if not settings.api_football_key:
            return self.skipped("API_FOOTBALL_KEY is missing. Add it to .env to collect provider data.")

        rows: list[dict] = []
        logs: list[dict] = []
        headers = {
            "X-RapidAPI-Key": settings.api_football_key,
            "X-RapidAPI-Host": settings.rapidapi_host,
        }
        base_url = f"https://{settings.rapidapi_host}/v3/players"

        for player in seed.to_dict("records"):
            params = {"search": player["player_name"], "season": season}
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=20)
                response.raise_for_status()
                payload = response.json()
                candidates = payload.get("response", [])
                if not candidates:
                    logs.append(self.log("EMPTY", f"No API-Football result for {player['player_name']}", base_url))
                    continue
                normalized = self._normalize(player, candidates[0], base_url)
                rows.append(normalized)
                logs.append(self.log("OK", f"Collected API-Football data for {player['player_name']}", base_url))
            except Exception as exc:
                logs.append(self.log("FAILED", f"{player['player_name']}: {exc}", base_url))

        return CollectorResult(self.name, pd.DataFrame(rows), pd.DataFrame(logs))

    def _normalize(self, seed_player: dict, item: dict, source_url: str) -> dict:
        player = item.get("player", {})
        stats = item.get("statistics", [{}])[0] if item.get("statistics") else {}
        games = stats.get("games", {})
        goals = stats.get("goals", {})
        team = stats.get("team", {})
        league = stats.get("league", {})

        return {
            "player_id": seed_player["player_id"],
            "age": player.get("age", "N/A"),
            "club": team.get("name", "N/A"),
            "league": league.get("name", "N/A"),
            "matches_played": games.get("appearences", "N/A"),
            "minutes_played": games.get("minutes", "N/A"),
            "goals": goals.get("total", "N/A"),
            "assists": goals.get("assists", "N/A"),
            "avg_rating": games.get("rating", "N/A"),
            "data_source": self.name,
            "source_url": source_url,
            "last_updated": utc_now(),
            "reliability": self.reliability,
            "collection_status": "REAL",
            "collection_notes": "Collected from API-Football via RapidAPI.",
        }
