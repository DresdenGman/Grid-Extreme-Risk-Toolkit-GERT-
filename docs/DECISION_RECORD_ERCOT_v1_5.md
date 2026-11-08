# Decision Record — ERCOT v1.5 probabilistic candidate: passes all preregistered gates

**Status:** Passes all preregistered gates (provisional candidate)
**Candidate:** `ercot-lag-residual-gbt-v1.5-candidate`
**Evidence:** [`evidence/ercot_v1_5_validation.json`](../evidence/ercot_v1_5_validation.json)
**Preregistration:** [`docs/PREREGISTRATION_ERCOT_v1_5.md`](PREREGISTRATION_ERCOT_v1_5.md)
**Promotion contract:** [`docs/PRODUCT_RELEASE_ACCEPTANCE.md`](PRODUCT_RELEASE_ACCEPTANCE.md)
**Evidence published:** 2026-11-08

## Context

The v1.5 candidate is a one-hour-ahead load-change quantile model anchored to
recent observed ERCOT load. It was evaluated on a frozen, blind 672-hour
window (2026-10-05 → 2026-11-01, 672 hourly observations). Model and
calibration parameters were frozen before the evaluation window was touched.

## Hypothesis

v1.4 showed strong pinball skill (0.76–0.84) but systematic under-coverage
at the upper tail (empirical coverage 0.865 / 0.906 / 0.958 against targets
0.90 / 0.95 / 0.99). Its calibration applied one fixed shrinkage factor per
quantile, frozen from a development evaluation — most severely at q99
(×0.55, the quantile with the largest shortfall). The hypothesis was that
**per-quantile recalibration on a dedicated, recent calibration window**
repairs coverage at the tail without giving up the skill, because the
failure is in the calibration constants, not in the center model.

## The single change

`ercot-lag-residual-gbt-v1.5-candidate` is identical to v1.4 in features,
target (one-hour-ahead ERCOT load change), center model class and
hyperparameters, and the frozen seasonal baseline. The single change is
calibration: for each served quantile (q50, q90, q95, q99), the residual-offset
multiplier was chosen **on the calibration window only**, by grid search
over [0.50, 1.50] in steps of 0.01, minimizing
|empirical coverage − target coverage| on that window, ties resolving to
the smaller multiplier. After scaling, residual offsets were kept in
non-decreasing order (isotonic ordering).

## Windows (frozen, UTC)

| Role | Window | Hours |
| --- | --- | --- |
| Training | Existing joined table, timestamps < 2025-01-01 (feature rows 2019-01-08 → 2024-12-31) | 52,434 |
| Calibration | 2026-09-07 00:00 → 2026-10-04 23:00 | 672 |
| Evaluation (blind) | 2026-10-05 00:00 → 2026-11-01 23:00 | 672 |

No window or gate was moved. No gaps were imputed.

## Data note

Pinned ERA5 had fully published 2026-10-31 and 2026-11-01 (verified
2026-11-08: all 48 hours, all four zones, all three variables, zero nulls)
and 2026-11-02, but had not yet published 2026-11-03. Weather for the run
was therefore downloaded for 2026-10-31 → 2026-11-02. The six load hours
2026-11-03 00:00–05:00 are unmatched by the inner join and excluded; they
lie outside every frozen window and do not affect any reported number.
Joined segment B runs 2026-08-28 05:00 → 2026-11-02 23:00 (1,603 rows);
both per-segment data-quality audits passed (strictly hourly, no missing
values, all checks true).

## Chosen multipliers and calibration coverage

Grid search on the calibration window only selected ×1.00 at every quantile
— the unscaled calibration-window residual quantiles were already the
closest to their targets, so no rescaling was needed.

| Quantile | Base residual offset (MW) | Chosen multiplier | Calibration coverage before | Calibration coverage after |
| --- | --- | --- | --- | --- |
| q50 | 138.70 | ×1.00 | 0.4033 | 0.5000 |
| q90 | 705.51 | ×1.00 | 0.8899 | 0.8988 |
| q95 | 886.92 | ×1.00 | 0.9315 | 0.9494 |
| q99 | 1,182.66 | ×1.00 | 0.8899 | 0.9896 |

"Before" is the v1.4 fixed shrinkage (×0.40 / ×0.90 / ×0.90 / ×0.55)
applied to the same calibration-window base offsets. "After" is the chosen
grid multipliers. The recalibration repaired the tail most: q99 calibration
coverage moved from 0.8899 to 0.9896 (target 0.99), and q50 from 0.4033 to
0.5000 (target 0.50). The hypothesis is confirmed on the calibration
window — and, as the blind evaluation below shows, it transferred.

## Promotion gates (predeclared)

Per the model promotion contract, a trained artifact may serve production
predictions only when **all** of the following pass on an untouched time window:

| Gate | Requirement |
|---|---|
| Pinball skill | skill > 0 vs frozen seasonal baseline at P50/P90/P95/P99 |
| Calibration | absolute empirical-coverage error ≤ 0.03 at every served quantile |
| Monotonicity | quantile-crossing rate ≤ 0.05 |
| Finiteness | finite outputs for every evaluation row |
| Evidence bundle | immutable metadata, evaluation, and backtest bundle |
| Feature availability | serving features built only from information available at prediction time |

## Observed evidence (blind evaluation, 672 hours)

| Quantile | Target coverage | Empirical coverage | Abs. coverage error | Pinball skill vs baseline | Wilson 95% CI (coverage) | Calibration gate (≤ 0.03) |
|---|---|---|---|---|---|---|
| P50 | 0.50 | 0.5089 | 0.0089 | 0.9304 | [0.4712, 0.5466] | ✅ pass |
| P90 | 0.90 | 0.9182 | 0.0182 | 0.9315 | [0.8950, 0.9366] | ✅ pass |
| P95 | 0.95 | 0.9568 | 0.0068 | 0.9330 | [0.9387, 0.9698] | ✅ pass |
| P99 | 0.99 | 0.9881 | 0.0019 | 0.9443 | [0.9767, 0.9940] | ✅ pass |

Additional gates: positive pinball skill at every quantile ✅ · quantile
crossings = 0 (rate 0.0) ✅ · finite outputs for all 672 evaluation rows ✅ ·
q50 MAE 321.70 MW · evidence bundle published in `evidence/` ✅ ·
serving features built only from information available at prediction time ✅.

## Decision

**Passes all preregistered gates.** The candidate is eligible for production
packaging under the promotion contract, and the artifact records
`validation_status: provisional_candidate`. The hypothesis is confirmed on
the blind window: per-quantile recalibration repaired the v1.4 tail
under-coverage (q99 blind coverage 0.9881 vs 0.9583 in v1.4; q90 0.9182 vs
0.8646) while pinball skill rose to 0.93–0.94 at every quantile.

This run publishes the evidence and opens the review pull request. It does
not place the artifact in `models/production/` and does not merge the pull
request — packaging and deployment remain a reviewed step.

## Consequences

- The v1.5 candidate is the first ERCOT candidate to pass every frozen
  gate, on a 672-hour blind window (seven times v1.4's 96 hours).
- Production prediction, scenario-analysis, and validated-backtest endpoints
  stay gated until the artifact is packaged and the pull request is reviewed
  and merged; they return unavailable, not fabricated output, in the
  meantime.
- The candidate is retained as research evidence with its full evaluation
  bundle public either way.

## Limitations

- GERT is decision-support research, not an autonomous grid controller.
- This record documents a model-governance decision, not a deployable
  forecast.
- Evaluation uses realized ERA5 weather for the target hour, as in v1.4,
  so results do not measure weather-forecast error and may be optimistic.
- With 672 evaluation hours, the expected number of q99 exceedances is
  ≈ 6.7, so the q99 coverage estimate is coarse (one observation ≈ 0.0015).
  Wilson 95% intervals are reported as context; the gate uses the point
  estimate against the same 0.03 tolerance, exactly as preregistered.
- Numbers above are rounded for readability; exact values live in the linked
  evidence JSON.

## Reproduction

```bash
python -m training.ercot.download_historical_weather_period \
  --start 2026-10-31 --end 2026-11-02 \
  --output-dir training_data/ercot_weather_era5_2026
# Join combined load (zone weights from <=2024 rows) with the 2019-2024
# and 2026 weather directories, split per segment, audit per segment,
# build features per segment, concatenate to training_runs/ercot_v1/features.csv
python -m training.ercot.train_quantile_model \
  --features training_runs/ercot_v1/features.csv \
  --calibration-mode grid --training-end 2025-01-01 \
  --calibration-start 2026-09-07 --calibration-end 2026-10-04 \
  --evaluation-start 2026-10-05 --evaluation-end 2026-11-01 \
  --model-version ercot-lag-residual-gbt-v1.5-candidate
```
