from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from morocco_ai_squad.config import SOFASCORE_RAW_DIR
from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult, utc_now


class SofascoreCollector(BaseCollector):
    name = "SofaScore"
    reliability = "MEDIUM"
    base_url = "https://www.sofascore.com/api/v1"

    def __init__(self, cache_enabled: bool = True) -> None:
        self.cache_enabled = cache_enabled
        SOFASCORE_RAW_DIR.mkdir(parents=True, exist_ok=True)

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
        session = self._session()

        for player in configured.to_dict("records"):
            player_name = player["player_name"]
            source_url = player.get("sofascore_url", "N/A")
            player_id = self._clean_id(player["sofascore_id"])
            try:
                payload = self._fetch_player_bundle(session, player_id, player_name)
                row = self._normalize(player, payload, source_url or f"{self.base_url}/player/{player_id}")
                fields_updated = sum(1 for key, value in row.items() if key != "player_id" and value not in ("N/A", "", None))
                rows.append(row)
                status = "SUCCESS" if fields_updated >= 8 else "PARTIAL"
                logs.append(
                    self.log(
                        status,
                        f"[INFO] {player_name} Source: SofaScore Status: {status} Fields updated: {fields_updated}",
                        source_url,
                        player_name,
                        fields_updated,
                    )
                )
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
            time.sleep(random.uniform(1.8, 3.2))

        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame.to_csv(SOFASCORE_RAW_DIR / "sofascore_players_normalized.csv", index=False, encoding="utf-8")
        return CollectorResult(self.name, frame, pd.DataFrame(logs))

    def _session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://www.sofascore.com",
                "Referer": "https://www.sofascore.com/",
            }
        )
        return session

    def _fetch_player_bundle(self, session: requests.Session, player_id: str, player_name: str) -> dict[str, Any]:
        cache_path = SOFASCORE_RAW_DIR / f"{player_id}.json"
        if self.cache_enabled and self._cache_fresh(cache_path):
            return json.loads(cache_path.read_text(encoding="utf-8"))

        endpoints = {
            "profile": f"{self.base_url}/player/{player_id}",
            "seasons": f"{self.base_url}/player/{player_id}/statistics/seasons",
            "search": f"{self.base_url}/search/all?q={requests.utils.quote(player_name)}&page=0",
        }
        bundle: dict[str, Any] = {"player_id": player_id, "fetched_at": utc_now(), "endpoints": {}}
        errors = []
        for key, url in endpoints.items():
            try:
                response = self._get_with_backoff(session, url)
                bundle["endpoints"][key] = response.json()
            except Exception as exc:
                errors.append(f"{key}: {exc}")
                bundle["endpoints"][key] = {"error": str(exc)}

        if all("error" in value for value in bundle["endpoints"].values()):
            raise RuntimeError("All SofaScore endpoints failed: " + " | ".join(errors))

        cache_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        return bundle

    def _get_with_backoff(self, session: requests.Session, url: str) -> requests.Response:
        waits = [0, 30, 60, 120]
        last_response = None
        for wait in waits:
            if wait:
                time.sleep(wait)
            response = session.get(url, timeout=25)
            last_response = response
            if response.status_code == 429:
                continue
            response.raise_for_status()
            return response
        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError(f"SofaScore request failed: {url}")

    def _cache_fresh(self, path: Path, max_age_hours: int = 24) -> bool:
        if not path.exists():
            return False
        modified = pd.Timestamp.fromtimestamp(path.stat().st_mtime, tz="UTC")
        return pd.Timestamp.utcnow() - modified < pd.Timedelta(hours=max_age_hours)

    def _clean_id(self, value) -> str:
        text = str(value).strip()
        if text.endswith(".0"):
            text = text[:-2]
        return text

    def _normalize(self, seed_player: dict, bundle: dict, source_url: str) -> dict:
        profile_payload = bundle.get("endpoints", {}).get("profile", {})
        payload = profile_payload.get("player", {}) if isinstance(profile_payload, dict) else {}
        search_payload = bundle.get("endpoints", {}).get("search", {})
        if not payload and isinstance(search_payload, dict):
            results = search_payload.get("results", [])
            for result in results:
                entity = result.get("entity", {})
                if str(entity.get("id")) == str(seed_player.get("sofascore_id")):
                    payload = entity
                    break

        team = payload.get("team") or {}
        date_of_birth = payload.get("dateOfBirthTimestamp")
        age = "N/A"
        if date_of_birth:
            age = int((pd.Timestamp.utcnow().timestamp() - int(date_of_birth)) / (365.25 * 24 * 3600))

        seasons_payload = bundle.get("endpoints", {}).get("seasons", {})
        latest_rating = "N/A"
        if isinstance(seasons_payload, dict):
            seasons = seasons_payload.get("seasons") or seasons_payload.get("uniqueTournamentSeasons") or []
            if seasons and isinstance(seasons, list):
                latest_rating = seasons[0].get("rating", "N/A") if isinstance(seasons[0], dict) else "N/A"

        return {
            "player_id": seed_player["player_id"],
            "player_name": payload.get("name", seed_player["player_name"]),
            "short_name": payload.get("shortName", seed_player.get("short_name", "N/A")),
            "age": age,
            "club": team.get("name", "N/A"),
            "league": "N/A",
            "primary_position": payload.get("position", seed_player.get("primary_position", "N/A")),
            "sofascore_rating": latest_rating,
            "avg_rating": latest_rating,
            "player_status": payload.get("status", "N/A"),
            "player_image": payload.get("imageUrl", "N/A"),
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
