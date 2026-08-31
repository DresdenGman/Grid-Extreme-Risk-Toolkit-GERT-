import numpy as np

from models.residual_quantile import ResidualQuantileBundle


class _DeltaEstimator:
    def predict(self, rows):
        return np.full(len(rows), 250.0)


def test_residual_bundle_anchors_to_latest_load_and_stays_monotonic() -> None:
    bundle = ResidualQuantileBundle(
        center_estimator=_DeltaEstimator(),
        residual_offsets_mw={"q50": 0.0, "q90": 500.0, "q95": 750.0, "q99": 1_250.0},
        anchor_feature_index=2,
    )

    prediction = bundle.predict_quantiles([[30.0, 5.0, 50_000.0]])

    assert prediction["q50"][0] == 50_250.0
    assert prediction["q99"][0] == 51_500.0
    assert prediction["q50"][0] <= prediction["q90"][0] <= prediction["q95"][0] <= prediction["q99"][0]
