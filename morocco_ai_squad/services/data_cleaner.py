from __future__ import annotations

import re
import unicodedata

import pandas as pd

from morocco_ai_squad.database.models import NA_VALUE


def normalize_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-zA-Z0-9 ]+", " ", ascii_value).lower().split())


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [
            "_".join([str(part) for part in col if str(part) and str(part) != "nan"]).strip("_")
            for col in data.columns
        ]
    data.columns = [clean_column_name(col) for col in data.columns]
    return data


def clean_column_name(column: str) -> str:
    text = str(column).replace("%", "pct")
    text = re.sub(r"[^0-9a-zA-Z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_").lower()
    return text or "unknown"


def remove_repeated_headers(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    for candidate in ["player", "Player"]:
        if candidate in data.columns:
            return data[data[candidate].astype(str).str.lower() != "player"]
    return data


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace(NA_VALUE, pd.NA), errors="coerce")


def completeness_by_row(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    return (~df.astype(str).isin([NA_VALUE, "", "nan", "None"])).mean(axis=1).round(3)
