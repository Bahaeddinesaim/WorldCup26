from __future__ import annotations

import json
import logging
import random
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


CACHE_ENABLED = True
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SQLITE_PATH = DATA_DIR / "cache" / "squad_data.sqlite"
SEED_CSV_PATH = DATA_DIR / "seed_players.csv"

FBREF_OUT = RAW_DIR / "fbref_moroccan_wc26.csv"
TRANSFERMARKT_OUT = RAW_DIR / "transfermarkt_moroccan_wc26.csv"
CAPOLOGY_OUT = RAW_DIR / "capology_moroccan_wc26.csv"
WHOSCORED_OUT = RAW_DIR / "whoscored_moroccan_wc26.csv"
MASTER_OUT = PROCESSED_DIR / "moroccan_players_wc26_master.csv"

USER_AGENT_TM = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
NA = "N/A"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("moroccan_players_scraper")


PLAYERS = [
    {"id": "gk_bounou", "name": "Yassine Bounou", "short": "Y. Bounou", "pos": "GK", "club": "Al Hilal", "league": "Saudi Pro League"},
    {"id": "gk_el_kajoui", "name": "Munir El Kajoui", "short": "M. El Kajoui", "pos": "GK", "club": "RS Berkane", "league": "Botola Pro"},
    {"id": "gk_tagnaouti", "name": "Ahmed Reda Tagnaouti", "short": "A. Tagnaouti", "pos": "GK", "club": "Wydad AC", "league": "Botola Pro"},
    {"id": "df_hakimi", "name": "Achraf Hakimi", "short": "A. Hakimi", "pos": "RB", "club": "Paris Saint-Germain", "league": "Ligue 1"},
    {"id": "df_mazraoui", "name": "Noussair Mazraoui", "short": "N. Mazraoui", "pos": "LB", "club": "Manchester United", "league": "Premier League"},
    {"id": "df_diop", "name": "Isa Diop", "short": "I. Diop", "pos": "CB", "club": "Fulham", "league": "Premier League"},
    {"id": "df_salah_eddine", "name": "Anass Salah-Eddine", "short": "Salah Eddine", "pos": "LB", "club": "Twente", "league": "Eredivisie"},
    {"id": "df_el_ouahdi", "name": "Zakaria El Ouahdi", "short": "Z. El Ouahdi", "pos": "RB", "club": "Genk", "league": "Belgian Pro League"},
    {"id": "df_halhal", "name": "Rachid Halhal", "short": "R. Halhal", "pos": "CB", "club": "TBD", "league": "TBD"},
    {"id": "df_aguerd", "name": "Nayef Aguerd", "short": "N. Aguerd", "pos": "CB", "club": "TBD", "league": "TBD"},
    {"id": "df_belammari", "name": "Youssef Belammari", "short": "Y. Belammari", "pos": "LB", "club": "Raja CA", "league": "Botola Pro"},
    {"id": "df_riad", "name": "Chadi Riad", "short": "C. Riad", "pos": "CB", "club": "Crystal Palace", "league": "Premier League"},
    {"id": "mf_el_aynaoui", "name": "Neil El Aynaoui", "short": "N. El Aynaoui", "pos": "CM", "club": "Lens", "league": "Ligue 1"},
    {"id": "mf_bouaddi", "name": "Ayyoub Bouaddi", "short": "A. Bouaddi", "pos": "CM", "club": "Lille", "league": "Ligue 1"},
    {"id": "mf_ounahi", "name": "Azzedine Ounahi", "short": "A. Ounahi", "pos": "CM", "club": "TBD", "league": "TBD"},
    {"id": "mf_el_khannouss", "name": "Bilal El Khannouss", "short": "B. El Khannouss", "pos": "AM", "club": "Leicester City", "league": "Premier League"},
    {"id": "mf_el_mourabet", "name": "Sofian El Mourabet", "short": "S. El Mourabet", "pos": "DM", "club": "TBD", "league": "TBD"},
    {"id": "mf_saibari", "name": "Ismael Saibari", "short": "I. Saibari", "pos": "AM", "club": "PSV", "league": "Eredivisie"},
    {"id": "mf_amrabat", "name": "Sofyan Amrabat", "short": "S. Amrabat", "pos": "DM", "club": "TBD", "league": "TBD"},
    {"id": "fw_gessime", "name": "Yan Gessime", "short": "Y. Gessime", "pos": "RW", "club": "Dunkerque", "league": "Ligue 2"},
    {"id": "fw_talbi", "name": "Chemsdine Talbi", "short": "C. Talbi", "pos": "RW", "club": "Club Brugge", "league": "Belgian Pro League"},
    {"id": "fw_diaz", "name": "Brahim Diaz", "short": "B. Diaz", "pos": "AM", "club": "Real Madrid", "league": "La Liga"},
    {"id": "fw_ezzalzouli", "name": "Abde Ezzalzouli", "short": "A. Ezzalzouli", "pos": "LW", "club": "Real Betis", "league": "La Liga"},
    {"id": "fw_amaimouni", "name": "Amine Amaimouni", "short": "A. Amaimouni", "pos": "LW", "club": "TBD", "league": "TBD"},
    {"id": "fw_rahimi", "name": "Soufiane Rahimi", "short": "S. Rahimi", "pos": "LW", "club": "Al Ain", "league": "UAE Pro League"},
    {"id": "fw_el_kaabi", "name": "Ayoub El Kaabi", "short": "A. El Kaabi", "pos": "ST", "club": "Olympiacos", "league": "Super League Greece"},
    {"id": "res_al_harrar", "name": "Mehdi Al Harrar", "short": "M. Al Harrar", "pos": "GK", "club": "Raja CA", "league": "Botola Pro"},
    {"id": "res_sbai", "name": "Abdellah Sbai", "short": "A. Sbai", "pos": "LB", "club": "TBD", "league": "TBD"},
    {"id": "res_saadane", "name": "Marouane Saadane", "short": "M. Saadane", "pos": "DM", "club": "FUS Rabat", "league": "Botola Pro"},
]


FBREF_PLAYER_URLS: dict[str, str | None] = {player["id"]: None for player in PLAYERS}
TRANSFERMARKT_SLUGS: dict[str, str | None] = {
    "gk_bounou": "yassine-bounou/profil/spieler/207834",
    "gk_el_kajoui": "munir-mohamedi/profil/spieler/167290",
    "gk_tagnaouti": "ahmed-reda-tagnaouti/profil/spieler/438902",
    "df_hakimi": "achraf-hakimi/profil/spieler/398073",
    "df_mazraoui": "noussair-mazraoui/profil/spieler/340456",
    "df_diop": "issa-diop/profil/spieler/272622",
    "df_salah_eddine": "anass-salah-eddine/profil/spieler/485584",
    "df_el_ouahdi": "zakaria-el-ouahdi/profil/spieler/742364",
    "df_halhal": None,
    "df_aguerd": "nayef-aguerd/profil/spieler/361914",
    "df_belammari": "youssef-belammari/profil/spieler/518804",
    "df_riad": "chadi-riad/profil/spieler/653325",
    "mf_el_aynaoui": "neil-el-aynaoui/profil/spieler/901019",
    "mf_bouaddi": "ayyoub-bouaddi/profil/spieler/1097139",
    "mf_ounahi": "azzedine-ounahi/profil/spieler/578915",
    "mf_el_khannouss": "bilal-el-khannouss/profil/spieler/847978",
    "mf_el_mourabet": None,
    "mf_saibari": "ismael-saibari/profil/spieler/659808",
    "mf_amrabat": "sofyan-amrabat/profil/spieler/287579",
    "fw_gessime": None,
    "fw_talbi": "chemsdine-talbi/profil/spieler/743384",
    "fw_diaz": "brahim-diaz/profil/spieler/314678",
    "fw_ezzalzouli": "abdessamad-ezzalzouli/profil/spieler/724656",
    "fw_amaimouni": None,
    "fw_rahimi": "soufiane-rahimi/profil/spieler/522719",
    "fw_el_kaabi": "ayoub-el-kaabi/profil/spieler/357632",
    "res_al_harrar": None,
    "res_sbai": None,
    "res_saadane": None,
}
CAPOLOGY_SLUGS: dict[str, str | None] = {player["id"]: None for player in PLAYERS}
WHOSCORED_PLAYER_IDS: dict[str, int | None] = {player["id"]: None for player in PLAYERS}


FBREF_TABLES = {
    "standard": "stats_standard",
    "shooting": "stats_shooting",
    "passing": "stats_passing",
    "passing_types": "stats_passing_types",
    "gca": "stats_gca",
    "defense": "stats_defense",
    "possession": "stats_possession",
    "misc": "stats_misc",
}


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_cache_fresh(path: Path, max_age_hours: int = 24) -> bool:
    if not CACHE_ENABLED or not path.exists():
        return False
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - modified < timedelta(hours=max_age_hours)


def random_sleep(low: float, high: float) -> None:
    time.sleep(random.uniform(low, high))


def get_with_backoff(session: requests.Session, url: str, **kwargs) -> requests.Response:
    waits = [30, 60, 120]
    for attempt, wait_seconds in enumerate([0, *waits], start=1):
        if wait_seconds:
            logger.warning("HTTP 429/backoff: sleeping %ss before retrying %s", wait_seconds, url)
            time.sleep(wait_seconds)
        response = session.get(url, timeout=kwargs.pop("timeout", 30), **kwargs)
        if response.status_code != 429:
            response.raise_for_status()
            return response
        if attempt == len(waits) + 1:
            logger.error("HTTP 429 persisted after retries: %s", url)
            response.raise_for_status()
    raise RuntimeError(f"Unreachable backoff state for {url}")


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ["_".join([str(part) for part in col if str(part) != "nan"]).strip("_") for col in data.columns]
    data.columns = [clean_column(col) for col in data.columns]
    return data


def clean_column(value: str) -> str:
    text = str(value).replace("%", "pct")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_").lower()


def load_seed(seed_csv_path: str | Path = SEED_CSV_PATH) -> pd.DataFrame:
    seed = pd.read_csv(seed_csv_path)
    return seed.replace({"": np.nan}).fillna(NA)


def empty_export(path: Path, columns: list[str]) -> pd.DataFrame:
    df = pd.DataFrame(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8")
    return df


def scrape_fbref(seed_csv_path: str | Path = SEED_CSV_PATH, output_path: Path = FBREF_OUT) -> pd.DataFrame:
    ensure_dirs()
    if is_cache_fresh(output_path):
        logger.info("FBref cache fresh: %s", output_path)
        return pd.read_csv(output_path)

    seed = load_seed(seed_csv_path)
    rows: list[dict[str, Any]] = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT_TM})

    for player in tqdm(seed.to_dict("records"), desc="FBref players"):
        player_id = player["player_id"]
        player_name = player["player_name"]
        url = FBREF_PLAYER_URLS.get(player_id)
        if not url:
            logger.warning("FBref URL missing for %s", player_name)
            rows.append({"player_id": player_id, "player_name": player_name, "scraped_at": utc_now(), "fbref_status": "MISSING_URL"})
            continue

        player_frames = []
        try:
            response = get_with_backoff(session, url)
            if "Just a moment" in response.text:
                raise RuntimeError("FBref anti-bot page returned")
            tables = pd.read_html(StringIO(response.text))
            for idx, table in enumerate(tables):
                cleaned = flatten_columns(table)
                cleaned["fbref_table_index"] = idx
                player_frames.append(cleaned)

            combined = pd.concat(player_frames, axis=1) if player_frames else pd.DataFrame()
            combined = combined.loc[:, ~combined.columns.duplicated()]
            row = combined.head(1).to_dict("records")[0] if not combined.empty else {}
            row.update({"player_id": player_id, "player_name": player_name, "scraped_at": utc_now(), "fbref_status": "SUCCESS"})
            rows.append(row)
            logger.info("FBref SUCCESS | %s | fields=%s", player_name, len(row))
        except Exception as exc:
            logger.warning("FBref PARTIAL/FAILED | %s | %s", player_name, exc)
            rows.append({"player_id": player_id, "player_name": player_name, "scraped_at": utc_now(), "fbref_status": "FAILED", "fbref_error": str(exc)})
        random_sleep(4, 7)

    df = pd.DataFrame(rows).replace("", NA).fillna(NA)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return df


def scrape_transfermarkt(seed_csv_path: str | Path = SEED_CSV_PATH, output_path: Path = TRANSFERMARKT_OUT) -> pd.DataFrame:
    ensure_dirs()
    if is_cache_fresh(output_path):
        logger.info("TransferMarkt cache fresh: %s", output_path)
        return pd.read_csv(output_path)

    seed = load_seed(seed_csv_path)
    rows: list[dict[str, Any]] = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT_TM, "Accept-Language": "en-US,en;q=0.9"})

    for player in tqdm(seed.to_dict("records"), desc="TransferMarkt players"):
        player_id = player["player_id"]
        player_name = player["player_name"]
        slug = TRANSFERMARKT_SLUGS.get(player_id)
        if not slug:
            logger.warning("TransferMarkt slug missing for %s", player_name)
            rows.append({"player_id": player_id, "player_name": player_name, "tm_status": "MISSING_SLUG", "scraped_at": utc_now()})
            continue

        url = f"https://www.transfermarkt.com/{slug}"
        try:
            response = get_with_backoff(session, url)
            soup = BeautifulSoup(response.text, "html.parser")
            row = parse_transfermarkt_profile(player_id, player_name, soup, url)
            rows.append(row)
            logger.info("TransferMarkt SUCCESS | %s | fields=%s", player_name, len([v for v in row.values() if v not in (NA, None, '')]))
        except Exception as exc:
            logger.error("TransferMarkt FAILED | %s | %s", player_name, exc)
            rows.append({"player_id": player_id, "player_name": player_name, "tm_status": "FAILED", "tm_error": str(exc), "scraped_at": utc_now()})
        random_sleep(3, 6)

    df = pd.DataFrame(rows).replace("", NA).fillna(NA)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return df


def parse_transfermarkt_profile(player_id: str, player_name: str, soup: BeautifulSoup, source_url: str) -> dict[str, Any]:
    labels = [node.get_text(" ", strip=True) for node in soup.select(".data-header__label")]
    values = [node.get_text(" ", strip=True) for node in soup.select(".data-header__content")]
    facts = {label.split(":")[0].strip().lower(): value for label, value in zip(labels, values)}

    h1 = soup.select_one("h1")
    full_name = re.sub(r"^#\d+\s+", "", h1.get_text(" ", strip=True)) if h1 else player_name
    club_node = soup.select_one(".data-header__club a")
    market_node = soup.select_one(".data-header__market-value-wrapper")

    history = []
    for point in soup.select("[data-datum], .waehrung"):
        text = point.get_text(" ", strip=True)
        if text:
            history.append({"raw": text})

    return {
        "player_id": player_id,
        "player_name": player_name,
        "full_name": full_name,
        "dob": facts.get("date of birth/age", NA),
        "nationality": facts.get("citizenship", NA),
        "height": facts.get("height", NA),
        "foot": facts.get("foot", NA),
        "position": facts.get("position", NA),
        "current_club": club_node.get_text(" ", strip=True) if club_node else NA,
        "contract_until": facts.get("contract expires", NA),
        "market_value_eur": market_node.get_text(" ", strip=True) if market_node else NA,
        "market_value_history": json.dumps(history, ensure_ascii=False),
        "agent": facts.get("agent", NA),
        "injury_status_tm": facts.get("outfitter", NA),
        "transfermarkt_url": source_url,
        "tm_status": "SUCCESS",
        "scraped_at": utc_now(),
    }


def scrape_capology(seed_csv_path: str | Path = SEED_CSV_PATH, output_path: Path = CAPOLOGY_OUT) -> pd.DataFrame:
    ensure_dirs()
    if is_cache_fresh(output_path):
        logger.info("Capology cache fresh: %s", output_path)
        return pd.read_csv(output_path)

    seed = load_seed(seed_csv_path)
    rows: list[dict[str, Any]] = []
    not_found_capology: list[str] = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT_TM})

    for player in tqdm(seed.to_dict("records"), desc="Capology players"):
        player_id = player["player_id"]
        player_name = player["player_name"]
        slug = CAPOLOGY_SLUGS.get(player_id)
        if not slug:
            not_found_capology.append(player_name)
            rows.append({"player_id": player_id, "player_name": player_name, "capology_status": "MISSING_SLUG", "scraped_at": utc_now()})
            continue

        url = f"https://www.capology.com/player/{slug}/"
        try:
            response = get_with_backoff(session, url)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": player_name,
                    "weekly_gross_eur": extract_money_near(text, "Weekly Gross"),
                    "annual_gross_eur": extract_money_near(text, "Annual Gross"),
                    "currency": "EUR",
                    "contract_end": extract_contract_end(text),
                    "capology_url": url,
                    "capology_status": "SUCCESS",
                    "scraped_at": utc_now(),
                }
            )
        except Exception as exc:
            logger.warning("Capology FAILED | %s | %s", player_name, exc)
            not_found_capology.append(player_name)
            rows.append({"player_id": player_id, "player_name": player_name, "capology_status": "FAILED", "capology_error": str(exc), "scraped_at": utc_now()})
        random_sleep(3, 5)

    if not_found_capology:
        logger.warning("Capology not found: %s", ", ".join(not_found_capology))
    df = pd.DataFrame(rows).replace("", NA).fillna(NA)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return df


def extract_money_near(text: str, label: str) -> str:
    idx = text.lower().find(label.lower())
    window = text[idx : idx + 180] if idx >= 0 else text
    match = re.search(r"[€£$]\s?[\d,.]+[kKmM]?", window)
    return match.group(0) if match else NA


def extract_contract_end(text: str) -> str:
    match = re.search(r"(20\d{2})", text)
    return match.group(1) if match else NA


def scrape_whoscored(seed_csv_path: str | Path = SEED_CSV_PATH, output_path: Path = WHOSCORED_OUT) -> pd.DataFrame:
    ensure_dirs()
    if is_cache_fresh(output_path):
        logger.info("WhoScored cache fresh: %s", output_path)
        return pd.read_csv(output_path)

    seed = load_seed(seed_csv_path)
    rows: list[dict[str, Any]] = []
    try:
        import ScraperFC as sfc  # type: ignore

        scraperfc_available = True
        logger.info("ScraperFC available: %s", sfc)
    except Exception:
        scraperfc_available = False
        logger.warning("ScraperFC unavailable; WhoScored scraper will emit N/A rows unless IDs are implemented.")

    for player in tqdm(seed.to_dict("records"), desc="WhoScored players"):
        player_id = player["player_id"]
        player_name = player["player_name"]
        whoscored_id = WHOSCORED_PLAYER_IDS.get(player_id)
        if not whoscored_id:
            rows.append({"player_id": player_id, "player_name": player_name, "whoscored_status": "MISSING_ID", "scraped_at": utc_now()})
            continue
        try:
            # Hook point for ScraperFC/Selenium implementation once stable player IDs are provided.
            raise NotImplementedError("WhoScored player summary extraction requires stable player/team/season IDs.")
        except Exception as exc:
            logger.warning("WhoScored FAILED | %s | %s", player_name, exc)
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": player_name,
                    "rating": NA,
                    "goals_ws": NA,
                    "assists_ws": NA,
                    "key_passes": NA,
                    "dribbles_won": NA,
                    "aerial_won": NA,
                    "tackles": NA,
                    "interceptions": NA,
                    "man_of_the_match_count": NA,
                    "whoscored_status": "FAILED" if scraperfc_available else "SCRAPERFC_UNAVAILABLE",
                    "whoscored_error": str(exc),
                    "scraped_at": utc_now(),
                }
            )
        random_sleep(5, 9)

    df = pd.DataFrame(rows).replace("", NA).fillna(NA)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return df


def load_scraped_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def merge_all_sources(seed_csv_path: str | Path = SEED_CSV_PATH) -> pd.DataFrame:
    ensure_dirs()
    master = load_seed(seed_csv_path)
    for source_path in [FBREF_OUT, TRANSFERMARKT_OUT, CAPOLOGY_OUT, WHOSCORED_OUT]:
        scraped = load_scraped_csv(source_path)
        if scraped.empty or "player_id" not in scraped.columns:
            continue
        master = pd.merge(master, scraped, on="player_id", how="left", suffixes=("", f"_{source_path.stem}"))

    for col in list(master.columns):
        if col.endswith("_transfermarkt_moroccan_wc26") or col.endswith("_fbref_moroccan_wc26"):
            continue

    master["data_confidence"] = master.apply(confidence_score, axis=1)
    master = master.replace("", NA).fillna(NA)
    master.to_csv(MASTER_OUT, index=False, encoding="utf-8")
    save_to_sqlite(master, "moroccan_players_wc26_master")
    return master


def confidence_score(row: pd.Series) -> str:
    data_status = str(row.get("data_status", "")).lower()
    scraped_statuses = " ".join(str(row.get(col, "")) for col in row.index if col.endswith("_status"))
    has_scraped = "SUCCESS" in scraped_statuses
    if data_status == "manual" and has_scraped:
        return "high"
    if data_status == "estimated" and has_scraped:
        return "medium"
    return "low"


def save_to_sqlite(df: pd.DataFrame, table_name: str) -> None:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(SQLITE_PATH) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)


def main() -> pd.DataFrame:
    ensure_dirs()
    logger.info("Starting Morocco WC2026 multi-source scraping pipeline")
    scrape_fbref()
    scrape_transfermarkt()
    scrape_capology()
    scrape_whoscored()
    master = merge_all_sources()
    logger.info("Pipeline complete: %s rows exported to %s", len(master), MASTER_OUT)
    return master


if __name__ == "__main__":
    main()
