"""Serializable monotonic residual-quantile bundle for GERT v1.3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class ResidualQuantileBundle:
    """Predict one conditional center and add ordered calibrated residuals.

    Fixed, ordered residual offsets make quantile crossing impossible by
    construction while the center model captures nonlinear weather, calendar,
    and causal load-lag effects.
    """

    center_estimator: Any
    residual_offsets_mw: dict[str, float]
    anchor_feature_index: int

    def predict_quantiles(self, rows: Any) -> dict[str, np.ndarray]:
        matrix = np.asarray(rows, dtype=float)
        if matrix.ndim != 2:
            raise ValueError("Expected a 2D feature matrix")
        center = (
            matrix[:, self.anchor_feature_index]
            + np.asarray(self.center_estimator.predict(matrix), dtype=float)
        )
        return {
            key: center + float(self.residual_offsets_mw[key])
            for key in ("q50", "q90", "q95", "q99")
        }
