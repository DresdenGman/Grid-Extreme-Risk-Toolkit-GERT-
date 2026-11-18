"""Export hourly rows from the frozen v1.5 regeneration without changing any parameter.

Reuses the repository's own split, baseline, and monotonic functions and the
model.joblib written by the frozen train_quantile_model command. It does not
fit anything new except confirming the saved center is reproduced.
"""
import csv, json, sys
from pathlib import Path
import joblib, numpy as np, pandas as pd

sys.path.insert(0, "/workspace/gert-v15")
from training.ercot import train_quantile_model as t
from training.ercot.features import SERVED_FEATURE_COLUMNS

FEATURES = Path(sys.argv[1]); ARTIFACT = Path(sys.argv[2]); OUT = Path(sys.argv[3])
frame = pd.read_csv(FEATURES)
training, calibration, evaluation = t.split_calibration_evaluation_windows(
    frame, "2025-01-01", "2026-09-07", "2026-10-04", "2026-10-05", "2026-11-01")
fn = list(SERVED_FEATURE_COLUMNS)
bundle = joblib.load(ARTIFACT / "model.joblib")
offs = bundle.residual_offsets_mw

def center(df):
    return bundle.center_estimator.predict(df[fn].to_numpy(dtype=float)) + df["lag_load_1h"].to_numpy(dtype=float)

c_eval = center(evaluation)
raw = {k: c_eval + v for k, v in offs.items()}
pred, crossing = t.monotonic_predictions(raw)
base = t.seasonal_baseline(training, evaluation)
OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "evaluation_rows.csv").open("w", newline="") as h:
    w = csv.writer(h)
    w.writerow(["timestamp_utc", "actual_load_mw", "center_prediction_mw",
                *[f"pred_{k}" for k in t.QUANTILE_KEYS.values()],
                *[f"baseline_{k}" for k in t.QUANTILE_KEYS.values()]])
    for i in range(len(evaluation)):
        w.writerow([evaluation.iloc[i]["timestamp_utc"], repr(float(evaluation.iloc[i]["actual_load_mw"])), repr(float(c_eval[i])),
                    *[repr(float(pred[k][i])) for k in t.QUANTILE_KEYS.values()],
                    *[repr(float(base[k][i])) for k in t.QUANTILE_KEYS.values()]])
c_cal = center(calibration)
with (OUT / "calibration_rows.csv").open("w", newline="") as h:
    w = csv.writer(h)
    w.writerow(["timestamp_utc", "actual_load_mw", "center_prediction_mw"])
    for i in range(len(calibration)):
        w.writerow([calibration.iloc[i]["timestamp_utc"], repr(float(calibration.iloc[i]["actual_load_mw"])), repr(float(c_cal[i]))])
# Confirm that a refit with the frozen function reproduces the saved center exactly.
refit = t.fit_center_estimator(training, fn)
same = bool(np.array_equal(refit.predict(evaluation[fn].to_numpy(dtype=float)),
                           bundle.center_estimator.predict(evaluation[fn].to_numpy(dtype=float))))
print(json.dumps({"evaluation_rows": len(evaluation), "calibration_rows": len(calibration),
                  "training_rows": len(training), "crossing_rate": crossing,
                  "refit_center_bit_identical": same}))
