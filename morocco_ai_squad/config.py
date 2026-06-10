from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = ROOT_DIR / "assets"
SEED_PLAYERS_PATH = DATA_DIR / "seed_players.csv"
SQLITE_PATH = DATA_DIR / "morocco_squad.db"


@dataclass(frozen=True)
class Settings:
    ai_provider: str = "offline"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    api_football_key: str | None = None


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    return Settings(
        ai_provider=os.getenv("AI_PROVIDER", "offline").lower(),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        api_football_key=os.getenv("API_FOOTBALL_KEY") or None,
    )
