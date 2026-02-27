from __future__ import annotations

from typing import Dict


def enforce_quantile_monotonicity(q: Dict[str, float]) -> Dict[str, float]:
    """
    Enforce monotonicity for the standard quantile keys: q50 <= q90 <= q95 <= q99.

    This function is intentionally centralized so every model output goes through the same fix-up.
    """
    keys = ["q50", "q90", "q95", "q99"]
    values = [float(q[k]) for k in keys]
    if values[3] >= values[2] >= values[1] >= values[0]:
        return {k: float(q[k]) for k in keys}

    sorted_vals = sorted(values)
    return dict(zip(keys, sorted_vals))

