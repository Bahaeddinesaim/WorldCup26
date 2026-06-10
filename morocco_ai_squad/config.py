from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
SEED_PLAYERS_PATH = DATA_DIR / "seed_players.csv"
PLAYERS_SEED_PATH = DATA_DIR / "players_seed.csv"
FBREF_RAW_DIR = DATA_DIR / "fbref_raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"
SOFASCORE_RAW_DIR = DATA_DIR / "raw" / "sofascore"
SQLITE_PATH = CACHE_DIR / "squad_data.sqlite"


@dataclass(frozen=True)
class Settings:
    ai_provider: str = "offline"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    api_football_key: str | None = None
    rapidapi_host: str = "api-football-v1.p.rapidapi.com"
    football_data_base_url: str = "https://www.football-data.co.uk"


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    return Settings(
        ai_provider=os.getenv("AI_PROVIDER", "offline").lower(),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        api_football_key=os.getenv("API_FOOTBALL_KEY") or None,
        rapidapi_host=os.getenv("RAPIDAPI_HOST", "api-football-v1.p.rapidapi.com"),
        football_data_base_url=os.getenv("FOOTBALL_DATA_BASE_URL", "https://www.football-data.co.uk"),
    )
