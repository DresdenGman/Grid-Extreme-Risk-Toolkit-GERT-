# GERT public-product release contract

GERT is releasable to general users only when the product is useful without
misrepresenting data, model authority, or operational maturity. A polished UI
is not a substitute for these requirements.

## Truth-state contract

Every user-visible result must identify three independent states:

1. **Data** — official live, external forecast, estimated fallback, or simulated.
2. **Model** — validated production artifact, gated candidate, unavailable, or simulated.
3. **Capacity** — official adequacy value, configured reference, or simulated.

Simulation is allowed only in an explicitly selected presentation mode. Live
mode must never substitute simulated predictions, backtests, or
historical events after a service failure.

## Model promotion contract

A trained artifact may be packaged as production only when all frozen gates pass
on an untouched time window:

- positive pinball skill against the frozen seasonal baseline at P50/P90/P95/P99;
- absolute empirical-coverage error no greater than 0.03 at every served quantile;
- quantile-crossing rate no greater than 0.05;
- finite outputs for every evaluation row;
- an immutable metadata, evaluation, and backtest evidence bundle;
- serving features that are constructed from information available at prediction time.

Observed windows cannot later be relabeled as untouched holdouts. A failed gate
does not become a pass by changing the threshold after inspecting results.

## Public API contract

- Production rejects wildcard CORS and unknown model modes.
- Secrets remain server-side and are never returned in errors or diagnostics.
- Expensive endpoints are rate-limited.
- Unavailable optional capabilities return a clear 503, not fabricated output.
- `/ready` verifies required dependencies; `/status` reports capabilities without secrets.
- Client errors use stable public messages and a request ID; internal exception text stays in logs.

## Frontend contract

- The canonical URL runs the same release as the backend.
- Live mode remains useful when prediction is gated by showing official load,
  capacity context, timestamps, provenance, and the reason prediction is unavailable.
- Scenario, benchmark, and event surfaces expose their evidence status.
- Loading, empty, stale, rate-limited, and offline states are actionable.
- Keyboard navigation, responsive layouts, contrast, and reduced-motion behavior are verified.

## Deployment acceptance

Before a production release:

1. Python and frontend tests pass.
2. The production frontend build passes.
3. `npm audit --audit-level=high` reports no high or critical vulnerabilities.
4. Container health, readiness, CORS, and security-header checks pass.
5. No tracked secret or production credential is present.
6. The deployed Git commit is recorded and matches the intended release.
7. Canonical frontend, backend `/health`, `/ready`, `/status`, prediction behavior,
   and provenance labels are verified from outside the local machine.
