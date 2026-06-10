from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class CollectorResult:
    collector: str
    rows: pd.DataFrame
    logs: pd.DataFrame


class BaseCollector:
    name = "base"
    reliability = "LOW"

    def log(self, status: str, message: str, source_url: str = "N/A") -> dict:
        return {
            "collector": self.name,
            "status": status,
            "message": message,
            "source_url": source_url,
            "last_updated": utc_now(),
        }

    def skipped(self, message: str, source_url: str = "N/A") -> CollectorResult:
        return CollectorResult(
            collector=self.name,
            rows=pd.DataFrame(),
            logs=pd.DataFrame([self.log("SKIPPED", message, source_url)]),
        )

    def failed(self, message: str, source_url: str = "N/A") -> CollectorResult:
        return CollectorResult(
            collector=self.name,
            rows=pd.DataFrame(),
            logs=pd.DataFrame([self.log("FAILED", message, source_url)]),
        )
