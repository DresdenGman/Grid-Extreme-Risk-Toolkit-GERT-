from __future__ import annotations

from dataclasses import dataclass

from domain.types import RiskLevel
from risk.config import (
    RISK_EXTREME_THRESHOLD,
    RISK_HIGH_THRESHOLD,
    RISK_MODERATE_THRESHOLD,
    RISK_SCORE_MARGIN_SCALE_MW,
)


@dataclass(frozen=True)
class RiskResult:
    level: RiskLevel
    score: float


class RiskScorer:
    """
    Decision rule engine: score/level is a business rule, not a model artifact.
    Thresholds and scaling are configurable via env vars (see risk/config.py).
    """

    def score(self, p99_load_mw: float, capacity_mw: float) -> RiskResult:
        margin = capacity_mw - p99_load_mw
        if margin <= 0:
            score = 100.0
        else:
            score = max(0.0, 100.0 - (margin / RISK_SCORE_MARGIN_SCALE_MW * 100.0))

        if score >= RISK_EXTREME_THRESHOLD:
            level = RiskLevel.EXTREME
        elif score >= RISK_HIGH_THRESHOLD:
            level = RiskLevel.HIGH
        elif score >= RISK_MODERATE_THRESHOLD:
            level = RiskLevel.MODERATE
        else:
            level = RiskLevel.LOW

        # Keep the public API shape stable (1 decimal rounding done at service layer).
        return RiskResult(level=level, score=float(score))

