# Preregistration — ERCOT v1.5 candidate

**Correction, 2026-11-10.** The commit that added this file
(`2fcf2c9b528c1e309fc9912687466ad69d7899c2`) has committer timestamp
2026-11-05 03:11:19 PT (2026-11-05T11:11:19Z), which is after the
evaluation window below closed at 2026-11-01 23:00 UTC. The status line
that follows is the historical claim. The timestamp does not support it.
This file is a retrospective freeze. The decision is in
[the v1.5 decision record](DECISION_RECORD_ERCOT_v1_5.md): evidence only,
not packaged, endpoints stay gated. The v1.4 rejection is unchanged. The
text below this correction is the original document.

**Status:** Frozen before any v1.5 training, calibration, or evaluation.
This document is committed to the repository before the data for the
calibration and evaluation windows is downloaded. Any amendment must be
committed and dated before evaluation results are inspected; amendments
after inspection are not permitted.

**Predecessor:** v1.4, rejected by its own preregistered gate
([decision record](DECISION_RECORD_ERCOT_v1_4.md),
[evidence](../evidence/ercot_v1_4_validation.json)).

## Hypothesis

v1.4 showed strong pinball skill (0.76–0.84) but systematic under-coverage
at the upper tail (empirical coverage 0.865 / 0.906 / 0.958 against targets
0.90 / 0.95 / 0.99). Its calibration applied one fixed shrinkage factor per
quantile, frozen from a development evaluation — most severely at q99
(×0.55, the quantile with the largest shortfall). The hypothesis is that
**per-quantile recalibration on a dedicated, recent calibration window**
repairs coverage at the tail without giving up the skill, because the
failure is in the calibration constants, not in the center model.

## The candidate — one change only

`ercot-lag-residual-gbt-v1.5-candidate` is identical to v1.4 in features,
target (one-hour-ahead ERCOT load change), center model class and
hyperparameters (as recorded in the v1.4 artifact metadata), and the frozen
seasonal baseline. The single change is calibration:

- For each served quantile (q50, q90, q95, q99), the residual-offset
  multiplier is chosen **on the calibration window only**, by grid search
  over [0.50, 1.50] in steps of 0.01, minimizing
  |empirical coverage − target coverage| on that window. Ties resolve to
  the smaller multiplier.
- After scaling, residual offsets are kept in non-decreasing order
  (isotonic ordering), so quantile crossing is impossible by construction —
  and the crossing gate is still evaluated and reported.

No other design choice is open. Anything not specified here is inherited
from v1.4 unchanged.

## Data windows (UTC, fixed in advance)

| Role | Window | Hours |
| --- | --- | --- |
| Training | Existing joined table, timestamps < 2025-01-01 (unchanged) | — |
| Calibration | 2026-09-07 00:00 → 2026-10-04 23:00 | 672 |
| Evaluation (frozen, blind) | 2026-10-05 00:00 → 2026-11-01 23:00 | 672 |

Neither 2026 window overlaps v1.4's evaluation window (2026-08-21 → 24) or
any earlier iteration's. If the contiguous hourly series for a window
cannot be assembled (the pipeline rejects gaps rather than imputing), the
run is aborted and this preregistration is amended — before any evaluation
— with the replacement window and the reason.

Known limitation, stated in advance: evaluation uses realized ERA5 weather
for the target hour, as in v1.4, so results do not measure weather-forecast
error and may be optimistic (see `docs/ERCOT_TRAINING.md`).

## Gates (unchanged from the promotion contract)

A candidate is promoted only if **all** of the following hold on the frozen
evaluation window:

| Gate | Requirement |
| --- | --- |
| Pinball skill | skill > 0 vs the frozen seasonal baseline at q50/q90/q95/q99 |
| Calibration | absolute empirical-coverage error ≤ 0.03 at every served quantile |
| Monotonicity | quantile-crossing rate ≤ 0.05 |
| Finiteness | finite outputs for every evaluation row |
| Evidence bundle | immutable metadata, evaluation, and backtest bundle published in `evidence/` |
| Feature availability | serving features built only from information available at prediction time |

## Reporting commitments

- All four quantiles are reported regardless of outcome.
- With 672 evaluation hours, the expected number of q99 exceedances is
  ≈ 6.7, so the q99 coverage estimate is coarse (one observation ≈ 0.0015).
  A binomial confidence interval for each coverage figure is reported as
  context. **The gate does not move**: the pass/fail rule is the point
  estimate against the same 0.03 tolerance, exactly as preregistered for
  v1.4.
- If any gate fails, the outcome is published as
  `docs/DECISION_RECORD_ERCOT_v1_5.md` recording a rejection, with the same
  completeness as the v1.4 record, and the inference endpoints stay gated.
- If all gates pass, promotion still requires the evidence bundle to be
  complete and reproducible from this repository; the decision record
  states what was verified, not just the headline numbers.
