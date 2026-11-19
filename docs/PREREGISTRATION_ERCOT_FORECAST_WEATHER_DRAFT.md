# DRAFT - awaiting owner approval

# Preregistration — ERCOT forecast-weather evaluation

**Status:** DRAFT - awaiting owner approval. Not frozen. Do not execute.

**Draft date:** 2026-11-10 (UTC). This file does not authorize downloading
the evaluation window, fitting or refitting a model, scoring the window, or
changing endpoint gating.

**Predecessor records:** [v1.4 remains rejected](DECISION_RECORD_ERCOT_v1_4.md).
[v1.5 is evidence only, not packaged](DECISION_RECORD_ERCOT_v1_5.md). Neither
decision is reopened by this draft.

## Purpose

The v1.5 scores used realized ERA5 weather for the target hour. Production
requests an Open-Meteo forecast (`data/ercot.py`, source
`external_forecast`). This draft specifies a later evaluation on archived
issued forecasts so that feature availability can be tested instead of
assumed. It is a proposal. It becomes a preregistration only if the owner
commits an approval that freezes the choices below before the window starts
and before any score from the window is inspected.

## Model freeze

Do not refit the center model. Do not rerun the multiplier grid. The
calibration multipliers are frozen at ×1.00 for q50, q90, q95, and q99.

The published base residual offsets, in MW, are:

| Quantile | Offset |
| --- | --- |
| q50 | 138.704963 |
| q90 | 705.51378 |
| q95 | 886.919353 |
| q99 | 1182.658076 |

Applying them requires the frozen center-model artifact from the v1.5 run
(`model.joblib` plus its metadata). That artifact is not in this repository.
If it cannot be recovered from the original training environment, stop.
A refit is a different candidate and needs its own preregistration. This
draft does not authorize one.

## Weather

Use archived **issued** forecasts, not reanalysis.

- Source: the Open-Meteo Historical Forecast API (previous model runs), or an
  equivalent archive of forecasts that were actually issued. An equivalent
  source is allowed only if the approval commit names the product, the model,
  and the lead time before the window starts.
- Same four ERCOT zones and the same variables as training: temperature,
  wind speed, and solar irradiance.
- Zone weights stay the weights fit on 2019–2024 load only.
- For each target hour T, the weather feature is a forecast issued at or
  before T − 1 hour, for hour T. Record the issue time and the lead.
- ERA5, the Open-Meteo historical archive, and any other realized
  target-hour analysis are not acceptable substitutes. If the one-hour-ahead
  issued forecast is missing, exclude the hour. Do not fill it with
  reanalysis.

## Proposed window

This window is a proposal. It had not started on the draft date.

| Role | Window (UTC) | Hours |
| --- | --- | --- |
| Evaluation | 2026-12-07 00:00 through 2027-01-03 23:00 | 672 |

No new calibration window is opened. The multipliers stay ×1.00.

Approval must be committed before 2026-12-07 00:00 UTC. The approval commit
must state that load and weather for the window have not been inspected. If
approval comes later, or if anyone has already looked at that interval,
discard the window and choose a later interval that has not started and has
not been inspected. Do that before computing any score.

## Baseline

Report both of the following on the same retained hours. Do not substitute
one for the other.

1. Month-hour seasonal baseline fit only on rows with timestamp before
   2025-01-01. This is the baseline behind the published v1.5 skill.
2. Month-hour seasonal baseline fit on every feature row strictly before the
   evaluation window. This is the rule in `split_evaluation_window` and
   `seasonal_baseline`, which is the v1.4 code path. v1.4's evidence file
   does not record that baseline's training end, so definition 2 is the code
   rule, not a recovered timestamp.

The promotion skill gate is skill > 0 at q50, q90, q95, and q99 against
baseline 2. Baseline 1 is reported in the same table. If baseline 2 cannot
be built, the skill gate does not pass.

## Gates

Thresholds are the existing promotion contract. They are not open for
revision after the window is scored.

| Gate | Requirement |
| --- | --- |
| Pinball skill | skill > 0 against baseline 2 at q50, q90, q95, and q99. Baseline 1 is reported beside it |
| Calibration | absolute empirical-coverage error ≤ 0.03 at every served quantile |
| Monotonicity | quantile-crossing rate ≤ 0.05 |
| Finiteness | finite outputs for every retained evaluation row |
| Evidence bundle | immutable metadata, hourly actuals, issued-forecast features, both baseline prediction series, model predictions, and a SHA-256 manifest. A summary JSON does not pass |
| Feature availability | every scored weather feature is an issued forecast available at the prediction origin. Realized target-hour weather fails this gate |

A failed gate stays a failure. The threshold is not moved after the scores
are seen.

## Power analysis for Q99 at n = 672

The Q99 gate fails when the absolute coverage error is greater than 0.03.
At n = 672 that is 27 or more exceedances: 27/672 gives error 0.030179 and
26/672 gives 0.028690. The figures below are IID binomial probabilities
from `scripts/recompute_ercot_v1_5_evidence.py`. Hourly errors are dependent,
so they illustrate the gate's sample size. They are not a deployment sample
size for extreme events.

| Assumed true Q99 coverage | P(gate fails) at n = 672 |
| --- | --- |
| 0.99 | 0.0000000023 |
| 0.96 | 0.5178 |
| 0.95 | 0.8989 |

True coverage 0.96 is the boundary of the 0.03 rule (0.99 − 0.03). At that
boundary the fail probability stays near one half as n grows. Choosing a
longer window does not fix the boundary case. It does raise power against a
true coverage of 0.95, which is already about 0.90 at n = 672.

If the owner selects a different n before approval, recompute these three
probabilities with the script and write the new figures into the approval
commit. Do not change 0.03 in order to raise the power.

## Exclusion

- An hour missing load, or missing an issued forecast for the target hour, is
  excluded.
- Excluded hours are listed by timestamp and counted. They are never imputed.
- Hours are not dropped because of the residual, the pinball contribution, or
  the coverage outcome.
- If any hour is excluded, the decision record states the retained n and the
  Q99 power at that n, computed with the same function, before interpreting
  the gate.
- If so many hours are missing that a contiguous issued-forecast series
  cannot be described, abort. Do not impute, and do not score a partial
  window until an amendment is committed.

## Reporting

- Report all four quantiles, both baselines, the retained n, the exclusion
  list, the forecast issue times, and the lead.
- Publish the row-level bundle and the manifest whether the gates pass or fail.
- If any gate fails, the outcome is a rejection record. Endpoints stay gated.
- If every gate passes, packaging is still a separate reviewed step. This
  draft does not place an artifact in `models/production/`.

## What this draft does not do

- It does not run the evaluation.
- It does not download the proposed window.
- It does not turn a failed gate into a pass.
- It does not soften the v1.4 rejection.
- It does not package the v1.5 candidate or open the gated endpoints.

## Approval

The owner replaces this status with a frozen preregistration in a commit that:

- is dated before 2026-12-07 00:00 UTC, or names a replacement window that
  has not yet started;
- states that the window has not been inspected;
- records the recovered model-artifact SHA-256, or stops because the artifact
  is gone;
- repeats the Q99 power figures for the chosen n.

Until that commit, this page is a draft.
