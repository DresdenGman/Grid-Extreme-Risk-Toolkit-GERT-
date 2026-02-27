from __future__ import annotations

import os


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


RISK_EXTREME_THRESHOLD = _get_float("RISK_EXTREME_THRESHOLD", 90.0)
RISK_HIGH_THRESHOLD = _get_float("RISK_HIGH_THRESHOLD", 75.0)
RISK_MODERATE_THRESHOLD = _get_float("RISK_MODERATE_THRESHOLD", 40.0)

RISK_SCORE_MARGIN_SCALE_MW = _get_float("RISK_SCORE_MARGIN_SCALE_MW", 5000.0)

VOLL_PRICE = _get_float("VOLL_PRICE", 9000.0)

