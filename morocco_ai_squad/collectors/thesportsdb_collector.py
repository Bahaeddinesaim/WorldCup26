from __future__ import annotations

import pandas as pd
import requests
import unicodedata

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult, utc_now


class TheSportsDBCollector(BaseCollector):
    name = "TheSportsDB"
    reliability = "MEDIUM"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        rows: list[dict] = []
        logs: list[dict] = []
        session = requests.Session()
        session.headers.update({"User-Agent": "MoroccoWorldCup26Analyzer/1.0"})

        for player in seed.to_dict("records"):
            player_name = player["player_name"]
            url = "https://www.thesportsdb.com/api/v1/json/123/searchplayers.php"
            try:
                response = session.get(url, params={"p": player_name}, timeout=20)
                response.raise_for_status()
                payload = response.json()
                candidates = payload.get("player") or []
                match = self._best_match(player_name, candidates)
                if not match:
                    logs.append(
                        self.log(
                            "FAILED",
                            f"[INFO] {player_name} Source: TheSportsDB Status: FAILED Detail: no player match",
                            response.url,
                            player_name,
                            0,
                        )
                    )
                    continue

                row = self._normalize(player, match, response.url)
                fields_updated = sum(1 for key, value in row.items() if key != "player_id" and value not in ("N/A", "", None))
                rows.append(row)
                logs.append(
                    self.log(
                        "SUCCESS",
                        f"[INFO] {player_name} Source: TheSportsDB Status: SUCCESS Fields updated: {fields_updated}",
                        response.url,
                        player_name,
                        fields_updated,
                    )
                )
            except Exception as exc:
                logs.append(
                    self.log(
                        "FAILED",
                        f"[INFO] {player_name} Source: TheSportsDB Status: FAILED Detail: {exc}",
                        url,
                        player_name,
                        0,
                    )
                )

        return CollectorResult(self.name, pd.DataFrame(rows), pd.DataFrame(logs))

    def _best_match(self, player_name: str, candidates: list[dict]) -> dict | None:
        if not candidates:
            return None
        normalized = self._normalize_name(player_name)
        morocco = [
            item
            for item in candidates
            if str(item.get("strSport", "")).lower() == "soccer"
            and str(item.get("strNationality", "")).lower() == "morocco"
        ]
        scored = []
        for item in morocco:
            score = self._name_score(normalized, self._normalize_name(str(item.get("strPlayer", ""))))
            if score >= 0.5:
                scored.append((score, item))
        if not scored:
            return None
        return sorted(scored, key=lambda pair: pair[0], reverse=True)[0][1]

    def _normalize(self, seed_player: dict, item: dict, source_url: str) -> dict:
        club = item.get("strTeam", "N/A")
        if isinstance(club, str) and club.startswith("_"):
            club = "N/A"
        return {
            "player_id": seed_player["player_id"],
            "player_name": item.get("strPlayer", seed_player["player_name"]),
            "short_name": seed_player.get("short_name", item.get("strPlayer", "N/A")),
            "age": self._age(item.get("dateBorn")),
            "club": club,
            "league": "N/A",
            "primary_position": self._map_position(item.get("strPosition", seed_player.get("primary_position", "N/A"))),
            "player_status": item.get("strStatus", "N/A"),
            "player_image": item.get("strCutout") or item.get("strThumb") or "N/A",
            "data_source": self.name,
            "source_url": source_url,
            "last_updated": utc_now(),
            "reliability": self.reliability,
            "collection_status": "REAL",
            "collection_notes": "Collected from TheSportsDB free V1 searchplayers endpoint.",
        }

    def _age(self, date_born: str | None):
        if not date_born:
            return "N/A"
        born = pd.to_datetime(date_born, errors="coerce", utc=True)
        if pd.isna(born):
            return "N/A"
        return int((pd.Timestamp.utcnow() - born).days / 365.25)

    def _map_position(self, position: str) -> str:
        mapping = {
            "Goalkeeper": "GK",
            "Right-Back": "RB",
            "Left-Back": "LB",
            "Centre-Back": "CB",
            "Defensive Midfield": "DM",
            "Central Midfield": "CM",
            "Attacking Midfield": "AM",
            "Right Winger": "RW",
            "Left Winger": "LW",
            "Forward": "ST",
            "Centre-Forward": "ST",
        }
        return mapping.get(position, position or "N/A")

    def _normalize_name(self, value: str) -> str:
        ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return " ".join(ascii_value.lower().replace("-", " ").split())

    def _name_score(self, expected: str, actual: str) -> float:
        if expected == actual:
            return 1.0
        expected_tokens = set(expected.split())
        actual_tokens = set(actual.split())
        if not expected_tokens or not actual_tokens:
            return 0.0
        return len(expected_tokens & actual_tokens) / len(expected_tokens | actual_tokens)
