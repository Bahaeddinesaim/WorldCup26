from __future__ import annotations

import re
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult, utc_now


class TransfermarktCollector(BaseCollector):
    name = "Transfermarkt"
    reliability = "HIGH"

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        configured = seed[seed["transfermarkt_url"].fillna("N/A") != "N/A"]
        if configured.empty:
            return CollectorResult(self.name, pd.DataFrame(), pd.DataFrame([self.log("FAILED", "No transfermarkt_url configured.")]))

        rows: list[dict] = []
        logs: list[dict] = []
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

        for player in configured.to_dict("records"):
            player_name = player["player_name"]
            url = str(player.get("transfermarkt_url", "N/A")).replace("transfermarkt.fr", "transfermarkt.com")
            if url in ("", "N/A"):
                logs.append(self.log("FAILED", f"[INFO] {player_name} Source: Transfermarkt missing URL", "N/A", player_name, 0))
                continue
            try:
                response = session.get(url, timeout=25)
                response.raise_for_status()
                row = self._parse_profile(player, response.text, url)
                fields_updated = sum(1 for key, value in row.items() if key != "player_id" and value not in ("N/A", "", None))
                status = "SUCCESS" if fields_updated >= 8 else "PARTIAL"
                rows.append(row)
                logs.append(
                    self.log(
                        status,
                        f"[INFO] {player_name} Source: Transfermarkt Status: {status} Fields updated: {fields_updated}",
                        url,
                        player_name,
                        fields_updated,
                    )
                )
            except Exception as exc:
                logs.append(
                    self.log(
                        "FAILED",
                        f"[INFO] {player_name} Source: Transfermarkt Status: FAILED Detail: {exc}",
                        url,
                        player_name,
                        0,
                    )
                )

        return CollectorResult(self.name, pd.DataFrame(rows), pd.DataFrame(logs))

    def _parse_profile(self, seed_player: dict, html: str, source_url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        labels = [node.get_text(" ", strip=True) for node in soup.select(".data-header__label")]
        values = [node.get_text(" ", strip=True) for node in soup.select(".data-header__content")]
        facts = {}
        for label, value in zip(labels, values):
            key = label.split(":")[0].strip().lower()
            facts[key] = value

        h1 = soup.select_one("h1")
        name = re.sub(r"^#\d+\s+", "", h1.get_text(" ", strip=True)) if h1 else seed_player["player_name"]
        if self._name_score(seed_player["player_name"], name) < 0.34:
            raise ValueError(f"Transfermarkt page name mismatch: expected {seed_player['player_name']}, got {name}")
        club = "N/A"
        club_node = soup.select_one(".data-header__club a")
        if club_node:
            club = club_node.get_text(" ", strip=True)

        age = "N/A"
        dob_age = facts.get("date of birth/age", "N/A")
        match = re.search(r"\((\d+)\)", dob_age)
        if match:
            age = int(match.group(1))

        market_value = "N/A"
        market_node = soup.select_one(".data-header__market-value-wrapper")
        if market_node:
            market_value = market_node.get_text(" ", strip=True)

        return {
            "player_id": seed_player["player_id"],
            "player_name": name,
            "short_name": seed_player.get("short_name", name),
            "age": age,
            "club": club,
            "league": facts.get("league level", "N/A"),
            "primary_position": self._map_position(facts.get("position", seed_player.get("primary_position", "N/A"))),
            "market_value": market_value,
            "transfer_history": f"Joined: {facts.get('joined', 'N/A')}; Contract expires: {facts.get('contract expires', 'N/A')}",
            "data_source": self.name,
            "source_url": source_url,
            "last_updated": utc_now(),
            "reliability": self.reliability,
            "collection_status": "REAL",
            "collection_notes": "Parsed public Transfermarkt profile page.",
        }

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
            "Centre-Forward": "ST",
        }
        return mapping.get(position, position or "N/A")

    def _normalize_name(self, value: str) -> str:
        ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return " ".join(ascii_value.lower().replace("-", " ").split())

    def _name_score(self, expected: str, actual: str) -> float:
        expected_tokens = set(self._normalize_name(expected).split())
        actual_tokens = set(self._normalize_name(actual).split())
        aliases = {
            "munir el kajoui": {"munir mohamedi", "munir"},
            "abdessamad ezzalzouli": {"abde ezzalzouli", "abdessamad ez zalzouli"},
        }
        expected_norm = self._normalize_name(expected)
        actual_norm = self._normalize_name(actual)
        if expected_norm == actual_norm or actual_norm in aliases.get(expected_norm, set()):
            return 1.0
        if not expected_tokens or not actual_tokens:
            return 0.0
        return len(expected_tokens & actual_tokens) / len(expected_tokens | actual_tokens)
