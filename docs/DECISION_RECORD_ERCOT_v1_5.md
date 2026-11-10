# Decision Record — ERCOT v1.5 probabilistic candidate: evidence only, not packaged

**Status:** evidence only, not packaged, endpoints stay gated
**Candidate:** `ercot-lag-residual-gbt-v1.5-candidate`
**Evidence:** [`evidence/ercot_v1_5_validation.json`](../evidence/ercot_v1_5_validation.json)
**Aggregate inputs and SHA-256 manifest:** [`evidence/ercot_v1_5/`](../evidence/ercot_v1_5/manifest.json)
**Preregistration:** [`docs/PREREGISTRATION_ERCOT_v1_5.md`](PREREGISTRATION_ERCOT_v1_5.md) (retrospective; see below)
**Promotion contract:** [`docs/PRODUCT_RELEASE_ACCEPTANCE.md`](PRODUCT_RELEASE_ACCEPTANCE.md)
**v1.4 record, unchanged:** [`docs/DECISION_RECORD_ERCOT_v1_4.md`](DECISION_RECORD_ERCOT_v1_4.md)
**Evidence first published:** 2026-11-08
**This correction:** 2026-11-10

This record replaces the 2026-11-08 claim that the candidate passed every
preregistered gate and was eligible for production packaging. No published
coverage, pinball loss, skill, MAE, residual offset, multiplier, or crossing
figure was edited. The v1.4 rejection is not softened.

## Decision

**Evidence only, not packaged, endpoints stay gated.**

The published 672-hour point estimates meet the numeric coverage, pinball-skill,
crossing, and finiteness checks. That is not a promotion. The evidence-bundle
gate and the feature-availability gate do not pass. The preregistration was
committed after the evaluation window had closed. Production prediction,
scenario-analysis, and validated-backtest endpoints stay gated. They return
unavailable, not fabricated output.

`ercot-delta-quantile-v1.4` remains rejected for production. Three of its four
calibration gates failed. The 0.03 tolerance is the same tolerance, and it was
not moved.

## Published point estimates (unchanged)

Blind window 2026-10-05 00:00 UTC through 2026-11-01 23:00 UTC, 672 hours.
Chosen multiplier ×1.00 at q50, q90, q95, and q99. Figures below are rounded;
exact values are in the evidence JSON.

| Quantile | Target | Empirical coverage | Abs. coverage error | Pinball skill vs pre-2025 baseline | Calibration point estimate (≤ 0.03) |
| --- | --- | --- | --- | --- | --- |
| P50 | 0.50 | 0.5089 | 0.0089 | 0.9304 | meets the point-estimate rule |
| P90 | 0.90 | 0.9182 | 0.0182 | 0.9315 | meets the point-estimate rule |
| P95 | 0.95 | 0.9568 | 0.0068 | 0.9330 | meets the point-estimate rule |
| P99 | 0.99 | 0.9881 | 0.0019 | 0.9443 | meets the point-estimate rule |

Published crossings: 0 (rate 0.0). Published q50 MAE: 321.70 MW. Published
claim: finite outputs on all 672 rows. Calibration-window coverage after the
×1.00 multipliers: q50 0.5000, q90 0.8988, q95 0.9494, q99 0.9896. Base
residual offsets: 138.70, 705.51, 886.92, and 1,182.66 MW.

Crossings, finiteness, pinball, MAE, offsets, and calibration coverage were
not recomputed from hourly rows. Those rows were not archived. The absolute
errors and skills above do match the published coverages and pinball losses.

## Gate table

| Gate | Result |
| --- | --- |
| Pinball skill > 0 | Point estimate meets the rule, against the pre-2025 baseline only |
| Absolute coverage error ≤ 0.03 | Point estimate meets the rule at every served quantile |
| Quantile-crossing rate ≤ 0.05 | Published rate is 0.0. Not recomputed from rows |
| Finite outputs | Published claim meets the rule. Not recomputed from rows |
| Evidence bundle | **Not passed.** The 2026-11-08 file is an aggregate summary. Hourly inputs and the model artifact were not published |
| Feature availability | **Not passed.** Evaluation weather is realized target-hour ERA5. Production weather is an Open-Meteo forecast |

## Why the earlier "all gates passed" claim was wrong

A review listed six problems. Each was checked against the repository, the
commit timestamps, and the published JSON. Nothing below changes a measured
number.

### Evidence bundle was over-claimed. Confirmed.

The promotion contract requires an immutable metadata, evaluation, and
backtest bundle. The training script writes `metadata.json`, `metrics.json`,
`evaluation_report.json`, `backtest_sample.json`, and `model.joblib`. None of
those files is in this repository (`training_runs/` is gitignored). The
published evidence file did not even list an evidence-bundle gate; the decision
record marked the gate passed anyway. Hourly actuals, model quantiles, and
baseline quantiles are also absent, so pinball, coverage, MAE, crossings, and
the calibration offsets cannot be recomputed from their inputs.

What was added here is the published aggregate bundle, a SHA-256 manifest, and
`scripts/recompute_ercot_v1_5_evidence.py`. The script recomputes every derived
number from those aggregates and checks the hashes. It does not, and cannot,
reconstruct the missing rows. The evidence-bundle gate stays **not passed**.

### Feature availability was over-claimed. Confirmed.

The same decision record marked "serving features built only from information
available at prediction time" as passed, and also said the evaluation uses
realized ERA5 weather for the target hour. Those statements disagree. The
training documentation and `train_quantile_model.py` state that historical
fits use realized ERA5 while production uses a one-hour weather forecast.
`data/ercot.py` requests `https://api.open-meteo.com/v1/forecast` and labels
it `external_forecast`. Realized target-hour weather is not available at the
prediction origin.

The published scores therefore omit weather-forecast error. They are an
optimistic upper bound on the skill and coverage that the same model would
show under the Open-Meteo forecast weather used at serve time. That
train/serve skew blocks packaging. The feature-availability gate stays
**not passed**.

### The preregistration is a retrospective freeze. Confirmed for the timestamp. Inspection before the commit was not established.

Commit `2fcf2c9b528c1e309fc9912687466ad69d7899c2` ("docs: preregister ERCOT
v1.5 candidate") has committer timestamp 2026-11-05 03:11:19 PT
(2026-11-05T11:11:19Z). The same timestamp is on GitHub. The evaluation window
is 2026-10-05 00:00 UTC through 2026-11-01 23:00 UTC, so the commit is after
the window closed. The document's status line says it was frozen before any
v1.5 training, calibration, or evaluation, and before the window's data was
downloaded. The timestamp does not support that status. A correction banner
on the preregistration points here; the original wording underneath is kept.

The results commit `98d4fbf82a78ebfaeca160bb0ac20915c8fc566e` is dated
2026-11-08T16:01:18Z. The calibration-code commit
`59e39d59c996b2134115f6475aca5c03542f07db` is dated 2026-11-05T11:23:49Z,
twelve minutes after the preregistration. Git does not show whether the
series had been inspected before the preregistration commit. What it shows
is that the freeze was written after the hours being scored had already
occurred.

### Q95 has 29 exceedances and Q99 has 8. Confirmed as the unique counts consistent with the published coverages. The Q99 gate's low power is confirmed.

At n = 672, the published six-decimal coverages match exactly one integer
count each:

| Quantile | Published coverage | Covered hours | Exceedances |
| --- | --- | --- | --- |
| Q95 | 0.956845 | 643 | 29 |
| Q99 | 0.988095 | 664 | 8 |

These counts are inferred from the rounded aggregates. There is no residual
file to count directly. The Wilson intervals in the JSON match those counts
to four decimal places.

The Q99 rule fails when the absolute coverage error is greater than 0.03.
With target 0.99 that is an exceedance count of 27 or more: 27/672 gives
error 0.030179, and 26/672 gives 0.028690. If true coverage were 0.96
(exceedance probability 0.04) and hours were independent,

P(fail) = P(Binomial(672, 0.04) ≥ 27) = 0.5178,

which is the review's figure of about 0.52. True coverage 0.96 sits on the
gate boundary, so a larger n does not move this probability toward 1. The
point-estimate rule is unchanged. The 0.9881 coverage is not relabeled as a
failure, and it is also not strong evidence of calibration.

### The 0.93 skill is against a weaker, earlier baseline. The level 2312 is confirmed. The 1276 and 0.874 figures are confirmed as arithmetic on a different window, and 0.874 is not a measured skill for these 672 hours.

The v1.5 command fits the seasonal baseline on timestamps before 2025-01-01
(`seasonal_baseline` on that training split). The published q50 baseline
pinball is 2312.438609. The published q50 model pinball is 160.851712. Skill
1 − 160.851712 / 2312.438609 = 0.930441, matching the JSON.

v1.4 publishes q50 MAE 404.535 MW and q50 skill 0.841492, and does not
publish baseline pinball. At q50, pinball loss is half of MAE, so the implied
baseline pinball on the **v1.4** 96-hour window is

(404.535 / 2) / (1 − 0.841492) = 1276.07.

Putting that other-window baseline under the v1.5 model pinball gives
1 − 160.851712 / 1276.07 = 0.8739, about 0.874. That substitution is not a
skill measured on the 672-hour window. v1.4's evidence file does not record
the baseline's training end, so this repository cannot show what a
v1.4-period baseline would have scored on October 2026. The limitation that
does stand: the reported 0.93 skill is not comparable to v1.4's 0.76–0.84
skill. v1.4's skill remains the skill of a rejected candidate.

## What would be required before packaging

Packaging would need a new evaluation, not a relabeling of this one. A draft
for that evaluation, using archived issued-forecast weather, is in
[`docs/PREREGISTRATION_ERCOT_FORECAST_WEATHER_DRAFT.md`](PREREGISTRATION_ERCOT_FORECAST_WEATHER_DRAFT.md).
It is not approved and it has not been run. Until a candidate passes every
gate, including feature availability and a complete row-level bundle, the
endpoints stay gated.

## Reproduction of the derived checks

```bash
python scripts/recompute_ercot_v1_5_evidence.py
```

The script checks the manifest hashes and rebuilds every derived number in
the evidence JSON. It exits non-zero if a published skill or coverage error
disagrees with the published pinball losses and coverages, or if v1.4 is no
longer recorded as `rejected_candidate`.

The original training command remains in the evidence JSON. It cannot be
rerun from this repository: the feature table and the ERCOT credential file
are not part of the commit, and this correction did not download either.
