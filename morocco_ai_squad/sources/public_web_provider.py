from __future__ import annotations

import pandas as pd
import requests
from bs4 import BeautifulSoup

from morocco_ai_squad.sources.base import PlayerDataProvider


class PublicWebProvider(PlayerDataProvider):
    """Conservative scaffold for legal public pages.

    This adapter intentionally avoids bypassing paywalls, login walls, robots
    policies or terms of service. Use it only with pages where collection is
    explicitly allowed, then normalize the result into the project schema.
    """

    name = "public_web"

    def __init__(self, allowed_urls: list[str] | None = None) -> None:
        self.allowed_urls = allowed_urls or []

    def fetch(self) -> pd.DataFrame:
        rows = []
        for url in self.allowed_urls:
            response = requests.get(url, timeout=15, headers={"User-Agent": "MoroccoSquadAnalyzer/0.1"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            rows.append({"source_url": url, "page_title": soup.title.string if soup.title else "", "data_status": "real"})
        return pd.DataFrame(rows)
