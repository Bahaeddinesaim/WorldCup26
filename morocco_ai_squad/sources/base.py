from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class PlayerDataProvider(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """Return player data with data_status and source_name columns."""
