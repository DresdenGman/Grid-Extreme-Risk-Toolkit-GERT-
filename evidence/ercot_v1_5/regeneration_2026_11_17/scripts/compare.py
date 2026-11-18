"""Recompute every published v1.5 metric from regenerated hourly rows and compare."""
import csv, json, math, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, "/workspace/gert-v15/scripts")
import recompute_ercot_v1_5_evidence as r  # repository's own Wilson/z

D = Path(sys.argv[1]); REPO = Path("/workspace/gert-v15")
pub = json.loads((REPO / "evidence/ercot_v1_5/measurements.json").read_text())
rep = json.loads((D / "artifact/evaluation_report.json").read_text())
meta = json.loads((D / "artifact/metadata.json").read_text())
TOL = 5.1e-7  # scripts/recompute_ercot_v1_5_evidence.py inferred_covered_count six-decimal tolerance
Q = {"q50": 0.5, "q90": 0.9, "q95": 0.95, "q99": 0.99}
SHRINK = {"q50": 0.40, "q90": 0.90, "q95": 0.90, "q99": 0.55}

def load(p):
    with open(p) as h: return list(csv.DictReader(h))
ev = load(D / "evaluation_rows.csv"); cal = load(D / "calibration_rows.csv")
y = np.array([float(x["actual_load_mw"]) for x in ev])
m = {k: np.array([float(x[f"pred_{k}"]) for x in ev]) for k in Q}
b = {k: np.array([float(x[f"baseline_{k}"]) for x in ev]) for k in Q}
yc = np.array([float(x["actual_load_mw"]) for x in cal]); cc = np.array([float(x["center_prediction_mw"]) for x in cal])

def pinball(y, p, a): d = y - p; return float(np.mean(np.maximum(a * d, (a - 1) * d)))
rows = []
def add(metric, published, regen, kind="float"):
    if kind == "int":
        ok = int(published) == int(regen); diff = abs(int(published) - int(regen))
    elif kind == "str":
        ok = published == regen; diff = None
    elif kind == "ci4":
        ok = [round(regen[0], 4), round(regen[1], 4)] == list(published)
        diff = max(abs(regen[0] - published[0]), abs(regen[1] - published[1]))
    else:
        diff = abs(float(published) - float(regen)); ok = diff <= TOL
    rows.append({"metric": metric, "published": published, "regenerated": regen, "abs_diff": diff, "match": bool(ok)})

n = len(y)
add("observations", pub["observations"], n, "int")
add("calibration_observations", pub["calibration_observations"], len(yc), "int")
add("calibration_window_start", pub["calibration_window_start"], cal[0]["timestamp_utc"], "str")
add("calibration_window_end", pub["calibration_window_end"], cal[-1]["timestamp_utc"], "str")
add("evaluation_window_start", pub["evaluation_window_start"], ev[0]["timestamp_utc"], "str")
add("evaluation_window_end", pub["evaluation_window_end"], ev[-1]["timestamp_utc"], "str")
add("q50_mae_mw", pub["q50_mae_mw"], float(np.mean(np.abs(y - m["q50"]))))
mat = np.column_stack([m[k] for k in Q]); cross = int(np.any(np.diff(mat, axis=1) < 0, axis=1).sum())
add("quantile_crossings", pub["quantile_crossings"], cross, "int")
add("quantile_crossing_rate", pub["quantile_crossing_rate"], cross / n)
finite = all(np.isfinite(v).all() for v in m.values())
add("finite_predictions_observed", pub["finite_predictions_observed"], f"all {n} evaluation rows finite" if finite else "non-finite present", "str")
pc = pub["calibration"]; rc = rep["calibration"]
add("calibration.mode", pc["mode"], rc["mode"], "str")
resid = yc - cc
for k, a in Q.items():
    base = float(np.quantile(resid, a))
    add(f"calibration.base_residual_offsets_mw.{k}", pc["base_residual_offsets_mw"][k], base)
    add(f"calibration.multipliers.{k}", pc["multipliers"][k], rc["multipliers"][k])
    add(f"calibration.calibration_coverage_after.{k}", pc["calibration_coverage_after"][k], float(np.mean(yc <= cc + rc["multipliers"][k] * base)))
    add(f"calibration.calibration_coverage_before.{k}", pc["calibration_coverage_before"][k], float(np.mean(yc <= cc + SHRINK[k] * base)))
for item in pub["quantile_metrics"]:
    k = item["quantile"]; a = Q[k]
    cov = float(np.mean(y <= m[k])); covered = int(np.sum(y <= m[k]))
    pl = pinball(y, m[k], a); bl = pinball(y, b[k], a)
    add(f"{k}.empirical_coverage", item["empirical_coverage"], cov)
    add(f"{k}.absolute_coverage_error", item["absolute_coverage_error"], abs(cov - a))
    add(f"{k}.pinball_loss", item["pinball_loss"], pl)
    add(f"{k}.baseline_pinball_loss", item["baseline_pinball_loss"], bl)
    add(f"{k}.pinball_skill_vs_baseline", item["pinball_skill_vs_baseline"], 1 - pl / bl)
    lo, hi = r.wilson_interval(covered, n)
    add(f"{k}.coverage_wilson_95_ci", item["coverage_wilson_95_ci"], [lo, hi], "ci4")
    add(f"{k}.target_coverage", item["target_coverage"], a)
# cross-check rows vs the frozen trainer's own report
consist = {k: (abs(rep["model"]["pinball_loss"][k] - pinball(y, m[k], Q[k])) < 1e-9 and
               abs(rep["baseline"]["pinball_loss"][k] - pinball(y, b[k], Q[k])) < 1e-9 and
               abs(rep["model"]["empirical_coverage"][k] - float(np.mean(y <= m[k]))) < 1e-12) for k in Q}
consist["q50_mae"] = abs(rep["q50_mae_mw"] - float(np.mean(np.abs(y - m["q50"])))) < 1e-9
repo = r.metrics_from_evaluation_rows(ev)
consist["repo_metrics_from_evaluation_rows"] = all(abs(repo[k]["pinball_loss"] - pinball(y, m[k], Q[k])) < 1e-9 and abs(repo[k]["baseline_pinball_loss"] - pinball(y, b[k], Q[k])) < 1e-9 and repo[k]["empirical_coverage"] == float(np.mean(y <= m[k])) for k in Q) and abs(repo["q50_mae_mw"] - float(np.mean(np.abs(y - m["q50"])))) < 1e-9 and repo["quantile_crossings"] == cross
allm = all(x["match"] for x in rows)
out = {"tolerance": {"float": TOL, "float_source": "scripts/recompute_ercot_v1_5_evidence.py inferred_covered_count (six-decimal uniqueness, 5.1e-7)",
                     "wilson_ci": "round(regenerated, 4) == published (script line ~233)", "integers_and_strings": "exact"},
       "rows_consistent_with_trainer_report": consist, "trainer_gates": rep["gates"],
       "all_published_metrics_reproduced": allm, "n_metrics": len(rows), "n_match": sum(x["match"] for x in rows), "metrics": rows}
(D / "comparison.json").write_text(json.dumps(out, indent=2) + "\n")
fmt = lambda v: "" if v is None else (f"[{v[0]:.6f}, {v[1]:.6f}]" if isinstance(v, list) and v and isinstance(v[0], float) else (f"{v:.10g}" if isinstance(v, float) else str(v)))
lines = ["# v1.5 published vs regenerated (2026-11-17)", "", f"Tolerance: floats |diff| <= {TOL} (repo six-decimal check); Wilson CI equal at 4 dp; counts/strings exact.", "",
         f"Result: {sum(x['match'] for x in rows)}/{len(rows)} match. All reproduced: {'yes' if allm else 'no'}.", "",
         "| metric | published | regenerated | abs diff | match |", "|---|---|---|---|---|"]
for x in rows:
    lines.append(f"| {x['metric']} | {fmt(x['published'])} | {fmt(x['regenerated'])} | {fmt(x['abs_diff'])} | {'yes' if x['match'] else 'NO'} |")
(D / "comparison.md").write_text("\n".join(lines) + "\n")
print(json.dumps({"all": allm, "n": len(rows), "match": sum(x["match"] for x in rows), "consist": consist}))
