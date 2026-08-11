"""Serializable trend-aware quantile model bundle used by real artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class TrendQuantileBundle:
    """Combine normalized-load estimators with an extrapolating annual trend.

    Tree models cannot extrapolate a year feature beyond their training range.
    The estimators therefore learn load as a ratio of that year's mean while
    this wrapper applies a log-linear annual scale at serving time.
    """

    estimators: dict[str, Any]
    trend_intercept: float
    trend_slope: float
    trend_base_year: int
    calibration_ratio: dict[str, float]
    year_feature_index: int

    def predict_quantiles(self, rows: Any) -> dict[str, np.ndarray]:
        matrix = np.asarray(rows, dtype=float)
        if matrix.ndim != 2 or matrix.shape[1] <= self.year_feature_index:
            raise ValueError("Expected a 2D feature matrix containing the year feature")
        years = matrix[:, self.year_feature_index]
        core = np.delete(matrix, self.year_feature_index, axis=1)
        scale = np.exp(
            self.trend_intercept
            + self.trend_slope * (years - float(self.trend_base_year))
        )
        return {
            key: estimator.predict(core) * scale
            + float(self.calibration_ratio.get(key, 0.0)) * scale
            for key, estimator in self.estimators.items()
        }
