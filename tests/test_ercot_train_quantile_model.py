import numpy as np
import pandas as pd

from training.ercot.train_quantile_model import metric_bundle, monotonic_predictions, split_periods


def test_monotonic_predictions_sorts_crossing_rows() -> None:
    fixed, rate = monotonic_predictions(
        {"q50": np.array([2.0]), "q90": np.array([1.0]), "q95": np.array([3.0]), "q99": np.array([4.0])}
    )

    assert rate == 1.0
    assert [fixed[key][0] for key in ("q50", "q90", "q95", "q99")] == [1.0, 2.0, 3.0, 4.0]


def test_metric_bundle_reports_pinball_and_coverage() -> None:
    y = np.array([1.0, 2.0])
    predictions = {key: np.array([1.0, 2.0]) for key in ("q50", "q90", "q95", "q99")}

    result = metric_bundle(y, predictions)

    assert result["pinball_loss"]["q50"] == 0.0
    assert result["empirical_coverage"]["q99"] == 1.0


def test_split_periods_accepts_a_fresh_evaluation_year() -> None:
    frame = pd.DataFrame(
        {
            "timestamp_utc": ["2025-01-01T06:00:00Z", "2026-01-01T06:00:00Z"],
            "actual_load_mw": [50_000.0, 51_000.0],
        }
    )

    training, evaluation = split_periods(frame, evaluation_year=2026)

    assert len(training) == 1
    assert len(evaluation) == 1
