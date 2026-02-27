from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, List, Tuple

from bulletin.templates import TEMPLATES


def simulate_extreme_window() -> Tuple[List[int], List[float], List[float], List[float]]:
    """
    Simulates a 24-hour window of a 'Polar Vortex' event.
    Returns: hours, P50 load, P99 load, Capacity
    """
    hours = list(range(24))
    p50_series: List[float] = []
    p99_series: List[float] = []
    capacity_series: List[float] = []

    for h in hours:
        base_load = 45000 + 10000 * math.sin((h - 6) / 24 * 2 * math.pi)

        if 17 <= h <= 21:
            volatility = 8000
            spike = 5000
        else:
            volatility = 2000
            spike = 0

        p50 = base_load + spike
        p99 = p50 + (volatility * 2.33)

        capacity = 58000 - (h * 100)

        p50_series.append(p50)
        p99_series.append(p99)
        capacity_series.append(capacity)

    return hours, p50_series, p99_series, capacity_series


def _risk_score(p99: float, capacity: float) -> float:
    margin = capacity - p99
    if margin <= 0:
        return 100.0
    return max(0.0, 100.0 - (margin / 5000.0 * 100.0))


def build_bulletin_context() -> Dict[str, object]:
    """
    Pure function: build the full bulletin context (numbers + copy decisions), no I/O.
    """
    hours, p50, p99, capacity = simulate_extreme_window()

    max_risk_score = 0.0
    for i in range(len(hours)):
        max_risk_score = max(max_risk_score, _risk_score(p99[i], capacity[i]))

    if max_risk_score >= 90:
        risk_level = "EXTREME"
    elif max_risk_score >= 75:
        risk_level = "HIGH"
    elif max_risk_score >= 40:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    risk_color = {"LOW": "#10b981", "MODERATE": "#f59e0b", "HIGH": "#f97316", "EXTREME": "#ef4444"}[risk_level]

    return {
        "issued_at": datetime.now(),
        "hours": hours,
        "p50": p50,
        "p99": p99,
        "capacity": capacity,
        "risk_level": risk_level,
        "max_risk_score": max_risk_score,
        "risk_color": risk_color,
        "templates": TEMPLATES,
    }

