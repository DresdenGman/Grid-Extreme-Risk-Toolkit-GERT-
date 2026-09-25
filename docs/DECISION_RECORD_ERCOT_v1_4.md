# Decision Record — ERCOT v1.4 probabilistic candidate: rejected for production

**Status:** Rejected for production inference
**Candidate:** `ercot-delta-quantile-v1.4`
**Evidence:** [`evidence/ercot_v1_4_validation.json`](../evidence/ercot_v1_4_validation.json)
**Promotion contract:** [`docs/PRODUCT_RELEASE_ACCEPTANCE.md`](PRODUCT_RELEASE_ACCEPTANCE.md)
**Evidence published:** 2026-08-30

## Context

The v1.4 candidate is a one-hour-ahead load-change quantile model anchored to
recent observed ERCOT load. It was evaluated on a frozen 96-hour window
(2026-08-21 → 2026-08-24, 96 hourly observations). Model and calibration
parameters were frozen before the final evaluation window was touched.

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

## Observed evidence

| Quantile | Target coverage | Empirical coverage | Abs. coverage error | Pinball skill vs baseline | Calibration gate (≤ 0.03) |
|---|---|---|---|---|---|
| P50 | 0.50 | 0.5208 | 0.0208 | 0.8415 | ✅ pass |
| P90 | 0.90 | 0.8646 | 0.0354 | 0.7578 | ❌ fail |
| P95 | 0.95 | 0.9063 | 0.0438 | 0.7848 | ❌ fail |
| P99 | 0.99 | 0.9583 | 0.0317 | 0.7683 | ❌ fail |

Additional gates: positive pinball skill at every quantile ✅ · quantile crossings = 0 ✅.

## Decision

**Rejected for production.** Three of four calibration gates failed. The candidate
showed strong predictive skill (pinball skill 0.76–0.84 across quantiles) but was
systematically under-covering at the upper tail — exactly the tail this project
exists to quantify.

## Why the bar was not lowered

The promotion contract states: *"A failed gate does not become a pass by changing
the threshold after inspecting results."* The 0.03 tolerance was fixed before
evaluation. Moving it to 0.045 after observing 0.0438 would have converted this
rejection into a pass — and destroyed the meaning of the gate.

## Consequences

- Production prediction, scenario-analysis, and validated-backtest endpoints
  remain **gated** (they return unavailable, not fabricated output).
- The candidate is retained as **research evidence only**, with its full
  evaluation bundle public.
- The 96-hour window is documented as insufficient evidence for promotion by
  itself, independent of the gate outcome.

## What would reverse this decision

A future candidate must, on a broader frozen evaluation window: pass the 0.03
calibration tolerance at every served quantile, keep positive pinball skill and
monotonicity, and ship the same immutable evidence bundle. No threshold will be
adjusted post hoc.

## Limitations

- GERT is decision-support research, not an autonomous grid controller.
- This record documents a model-governance decision, not a deployable forecast.
- Numbers above are rounded for readability; exact values live in the linked
  evidence JSON.
