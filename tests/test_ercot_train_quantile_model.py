import numpy as np
import pandas as pd

from training.ercot.features import SERVED_FEATURE_COLUMNS
from training.ercot.train_quantile_model import (
    choose_multiplier,
    grid_calibrated_offsets,
    grid_multipliers,
    metric_bundle,
    monotonic_predictions,
    split_periods,
)


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


def test_grid_multipliers_cover_the_preregistered_range() -> None:
    grid = grid_multipliers()

    assert len(grid) == 101
    assert grid[0] == 0.50
    assert grid[-1] == 1.50
    assert all(abs(b - a - 0.01) < 1e-9 for a, b in zip(grid, grid[1:]))


def test_choose_multiplier_hits_exact_target_coverage() -> None:
    center = np.zeros(100)
    actual = np.array([4.0] * 50 + [8.0] * 40 + [30.0] * 10)

    multiplier, coverage = choose_multiplier(actual, center, base_offset=10.0, target_coverage=0.9)

    assert multiplier == 0.80
    assert coverage == 0.90


def test_choose_multiplier_breaks_ties_toward_the_smaller_multiplier() -> None:
    center = np.zeros(100)
    actual = np.array([4.0] * 50 + [8.0] * 40 + [30.0] * 10)

    multiplier, coverage = choose_multiplier(actual, center, base_offset=10.0, target_coverage=0.7)

    # Coverage 0.50 (first reached at the grid minimum 0.50) and 0.90 are both
    # 0.20 from target; the tie must resolve to the smaller multiplier.
    assert multiplier == 0.50
    assert coverage == 0.50


def _synthetic_frame(rows: int, start: str, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(start, periods=rows, freq="h", tz="UTC")
    lag = 50_000.0 + np.cumsum(rng.normal(0.0, 50.0, rows))
    frame = pd.DataFrame(
        {
            "timestamp_utc": timestamps.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "actual_load_mw": lag + rng.normal(0.0, 100.0, rows),
        }
    )
    for column in SERVED_FEATURE_COLUMNS:
        frame[column] = rng.normal(0.0, 1.0, rows)
    frame["lag_load_1h"] = lag
    return frame


def test_grid_calibrated_offsets_are_ordered_and_in_range() -> None:
    training = _synthetic_frame(400, "2024-01-01", seed=1)
    calibration = _synthetic_frame(300, "2026-09-07", seed=2)

    offsets, details = grid_calibrated_offsets(training, calibration, list(SERVED_FEATURE_COLUMNS))

    values = [offsets[key] for key in ("q50", "q90", "q95", "q99")]
    assert values == sorted(values)
    assert details["mode"] == "grid"
    for key in ("q50", "q90", "q95", "q99"):
        assert 0.50 <= details["multipliers"][key] <= 1.50
        assert 0.0 <= details["calibration_empirical_coverage"][key] <= 1.0


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
