from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Mapping

from api.schemas import WeatherFeatures


class ModelInterface(ABC):
    @abstractmethod
    def predict(
        self,
        features: WeatherFeatures,
        timestamp: datetime | None = None,
        operational_features: Mapping[str, float] | None = None,
    ) -> Dict[str, float]:
        raise NotImplementedError

    def get_version(self) -> str:
        return "base-v0"

    def supports_region(self, region: str) -> bool:
        return True
