from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from api.schemas import WeatherFeatures


class ModelInterface(ABC):
    @abstractmethod
    def predict(self, features: WeatherFeatures) -> Dict[str, float]:
        raise NotImplementedError

    def get_version(self) -> str:
        return "base-v0"

