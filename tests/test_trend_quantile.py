import numpy as np
import pytest

from models.trend_quantile import TrendQuantileBundle


class _ConstantEstimator:
    def predict(self, rows):
        return np.ones(len(rows))


def test_trend_bundle_extrapolates_and_keeps_calibrated_order() -> None:
    estimator = _ConstantEstimator()
    bundle = TrendQuantileBundle(
        estimators={key: estimator for key in ("q50", "q90", "q95", "q99")},
        trend_intercept=float(np.log(50_000.0)),
        trend_slope=float(np.log(1.05)),
        trend_base_year=2024,
        calibration_ratio={"q50": 0.0, "q90": 0.1, "q95": 0.2, "q99": 0.3},
        year_feature_index=7,
    )

    result = bundle.predict_quantiles([[30, 4, 500, 12, 1, 7, 0, 2025]])

    assert result["q50"][0] == pytest.approx(52_500.0)
    assert result["q50"][0] < result["q90"][0] < result["q95"][0] < result["q99"][0]
