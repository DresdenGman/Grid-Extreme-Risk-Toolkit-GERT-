import pandas as pd

from training.ercot.audit_training_data import audit


def test_audit_accepts_two_valid_contiguous_rows() -> None:
    load = pd.DataFrame(
        {
            "actual_load_mw": [100.0, 100.0],
            "north_mw": [40.0, 40.0], "south_mw": [20.0, 20.0],
            "west_mw": [10.0, 10.0], "houston_mw": [30.0, 30.0],
        }
    )
    joined = pd.DataFrame(
        {
            "timestamp_utc": ["2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z"],
            "actual_load_mw": [100.0, 100.0],
            "temperature_c": [20.0, 21.0], "wind_speed_ms": [3.0, 4.0],
            "solar_irradiance_wm2": [0.0, 0.0],
        }
    )

    assert audit(load, joined)["passed"] is True
