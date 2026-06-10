from __future__ import annotations

from io import StringIO
from urllib.parse import quote

import pandas as pd
import requests

from morocco_ai_squad.collectors.base import BaseCollector, CollectorResult, utc_now
from morocco_ai_squad.config import FBREF_RAW_DIR, PROCESSED_DIR
from morocco_ai_squad.database.models import NA_VALUE
from morocco_ai_squad.services.data_cleaner import flatten_columns, normalize_name, remove_repeated_headers


FBREF_CATEGORIES = {
    "standard": ("stats", "div_stats_standard"),
    "shooting": ("shooting", "div_stats_shooting"),
    "passing": ("passing", "div_stats_passing"),
    "passing_types": ("passing_types", "div_stats_passing_types"),
    "gca": ("gca", "div_stats_gca"),
    "defense": ("defense", "div_stats_defense"),
    "possession": ("possession", "div_stats_possession"),
    "playing_time": ("playingtime", "div_stats_playing_time"),
    "misc": ("misc", "div_stats_misc"),
}


class FBrefPlayerStatsScraper(BaseCollector):
    name = "FBref"
    reliability = "HIGH"

    def __init__(self, competition_id: str = "Big5", competition_name: str = "Big-5-European-Leagues") -> None:
        self.competition_id = competition_id
        self.competition_name = competition_name
        FBREF_RAW_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def fetch(self, seed: pd.DataFrame) -> CollectorResult:
        raw_tables: dict[str, pd.DataFrame] = {}
        logs: list[dict] = []

        for category, (path, div_id) in FBREF_CATEGORIES.items():
            try:
                df = self._read_category(path, div_id)
                df = self._prepare_table(df, category)
                raw_tables[category] = df
                raw_path = FBREF_RAW_DIR / f"fbref_{category}.csv"
                df.to_csv(raw_path, index=False, encoding="utf-8")
                logs.append(self.log("SUCCESS", f"FBref {category} table scraped", str(raw_path), "ALL", len(df.columns)))
            except Exception as exc:
                logs.append(self.log("FAILED", f"FBref {category} failed: {exc}", self._page_url(path), "ALL", 0))

        if not raw_tables:
            return CollectorResult(self.name, pd.DataFrame(), pd.DataFrame(logs))

        merged = self._merge_tables(raw_tables)
        filtered = self._filter_seed_players(merged, seed)
        processed = self._normalize_for_app(filtered, seed)
        processed_path = PROCESSED_DIR / "fbref_player_stats_clean.csv"
        processed.to_csv(processed_path, index=False, encoding="utf-8")

        for row in processed.to_dict("records"):
            fields = sum(1 for value in row.values() if value not in (NA_VALUE, "", None))
            logs.append(
                self.log(
                    "SUCCESS" if fields > 8 else "PARTIAL",
                    f"[INFO] {row.get('player_name', 'N/A')} Source: FBref Fields updated: {fields}",
                    str(processed_path),
                    row.get("player_name", "N/A"),
                    fields,
                )
            )

        return CollectorResult(self.name, processed, pd.DataFrame(logs))

    def _read_category(self, path: str, div_id: str) -> pd.DataFrame:
        errors: list[str] = []
        for url in [self._widget_url(path, div_id), self._page_url(path)]:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                html = requests.get(url, headers=headers, timeout=30).text
                if "Just a moment" in html or "cf-browser-verification" in html:
                    raise RuntimeError("FBref returned anti-bot page")
                tables = pd.read_html(StringIO(html), header=1)
                if tables:
                    return tables[0]
            except Exception as exc:
                errors.append(f"{url}: {exc}")
        raise RuntimeError(" | ".join(errors))

    def _widget_url(self, path: str, div_id: str) -> str:
        fbref_path = f"/en/comps/{self.competition_id}/{path}/players/{self.competition_name}-Stats"
        return (
            "https://widgets.sports-reference.com/wg.fcgi?css=1&site=fb&url="
            f"{quote(fbref_path, safe='')}&div={div_id}"
        )

    def _page_url(self, path: str) -> str:
        return f"https://fbref.com/en/comps/{self.competition_id}/{path}/players/{self.competition_name}-Stats"

    def _prepare_table(self, df: pd.DataFrame, category: str) -> pd.DataFrame:
        data = flatten_columns(remove_repeated_headers(df))
        rename_map = {}
        for col in data.columns:
            if col in {"player", "nation", "pos", "squad", "comp", "age", "born"}:
                rename_map[col] = col
            else:
                rename_map[col] = f"fbref_{category}_{col}"
        data = data.rename(columns=rename_map)
        return data.loc[:, ~data.columns.duplicated()].drop_duplicates()

    def _merge_tables(self, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
        keys = [col for col in ["player", "nation", "pos", "squad", "comp", "age", "born"] if col in next(iter(tables.values())).columns]
        merged = next(iter(tables.values()))
        for table in list(tables.values())[1:]:
            join_keys = [key for key in keys if key in table.columns and key in merged.columns]
            if not join_keys:
                continue
            merged = pd.merge(merged, table, on=join_keys, how="outer")
            merged = merged.loc[:, ~merged.columns.str.endswith("_y")]
            merged.columns = merged.columns.str.replace("_x", "", regex=False)
        return merged.loc[:, ~merged.columns.duplicated()].drop_duplicates()

    def _filter_seed_players(self, df: pd.DataFrame, seed: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data["match_name"] = data["player"].apply(normalize_name)
        wanted = seed[["player_id", "player_name"]].copy()
        wanted["match_name"] = wanted["player_name"].apply(normalize_name)
        return pd.merge(wanted, data, on="match_name", how="inner", suffixes=("_seed", ""))

    def _normalize_for_app(self, df: pd.DataFrame, seed: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        data = df.copy().replace("", NA_VALUE).fillna(NA_VALUE)

        def col(*names: str) -> pd.Series:
            for name in names:
                if name in data.columns:
                    return data[name]
            return pd.Series([NA_VALUE] * len(data), index=data.index)

        out = pd.DataFrame(
            {
                "player_id": data["player_id"],
                "player_name": data["player_name_seed"],
                "age": col("age"),
                "club": col("squad"),
                "league": col("comp"),
                "primary_position": col("pos"),
                "matches_played": col("fbref_standard_mp", "fbref_playing_time_mp"),
                "minutes_played": col("fbref_standard_min", "fbref_playing_time_min"),
                "goals": col("fbref_standard_gls"),
                "assists": col("fbref_standard_ast"),
                "xg": col("fbref_standard_xg", "fbref_shooting_xg"),
                "xa": col("fbref_standard_xag", "fbref_passing_xag"),
                "defensive_actions": col("fbref_defense_tkl", "fbref_defense_tkl_int"),
                "offensive_actions": col("fbref_gca_sca", "fbref_possession_prgc"),
                "data_source": self.name,
                "source_url": "FBref Big 5 player standard category pages",
                "last_updated": utc_now(),
                "reliability": self.reliability,
                "collection_status": "REAL",
                "collection_notes": "Merged FBref standard, shooting, passing, passing types, GCA, defense, possession, playing time and misc tables.",
            }
        )
        return out.replace("", NA_VALUE).fillna(NA_VALUE)
