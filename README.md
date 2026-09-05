# Grid Extreme Risk Toolkit (GERT)

GERT is an evidence-first decision-support platform for power-grid tail risk. It combines official ERCOT operating context, probabilistic load research, scenario stress testing, event reconstruction, and explicit model-governance controls in one interface.

The product is built around a simple question: **how close is an unlikely but plausible demand tail to the system boundary?** Conventional dashboards emphasize a single expected-load line. GERT makes the P50–P99 uncertainty geometry, data provenance, capacity basis, and model authority visible.

> GERT is research and decision-support software, not autonomous grid control. Unvalidated, simulated, fallback, and unavailable states are labeled and never silently promoted to production authority.

## Public product state

- **Official operating context:** the backend can retrieve current ERCOT load and adequacy data with server-side ERCOT credentials.
- **Weather context:** live weather is retrieved from external public sources with timestamps and provenance.
- **Probabilistic model:** the latest `ercot-delta-quantile-v1.4` candidate is **rejected for production**. It demonstrated positive pinball skill at every reported quantile, but missed the predeclared ±3 percentage-point calibration tolerance at Q90, Q95, and Q99 on the frozen 96-hour evaluation window.
- **Production behavior:** prediction, scenario, and validated-backtest endpoints return an explicit `503` until a `validated_production` artifact is active.
- **Evidence:** sanitized candidate results remain public through `GET /model/evidence` and the Evidence page.
- **Presentation mode:** `?demo=1` is an explicit simulated mode for interface demonstrations. Live mode never falls back to simulated predictions after an error.

The release contract and promotion gates are documented in [`docs/PRODUCT_RELEASE_ACCEPTANCE.md`](docs/PRODUCT_RELEASE_ACCEPTANCE.md).

## Product surfaces

| Surface | Purpose | Authority |
| --- | --- | --- |
| Live Monitor | Official load, capacity context, weather, timestamps, and provenance | Operational context |
| Scenario Lab | Perturb weather and physical drivers through the active model contract | Gated until model validation |
| Event Replay | Explain how tail pressure can evolve during an extreme event | Labeled educational reconstruction |
| Evidence | Publish skill, coverage, promotion gates, provenance, and limitations | Versioned observed evidence |

## Mathematical core

GERT models a conditional distribution rather than only a conditional mean. For quantile level `q`, training minimizes pinball loss:

```text
Lq(y, y_hat) = max(q(y - y_hat), (q - 1)(y - y_hat))
```

The current research path predicts one-hour load change relative to the latest official load anchor and reconstructs ordered P50/P90/P95/P99 levels. Promotion requires all frozen gates to pass:

1. Positive pinball skill against the frozen month-hour baseline at every served quantile.
2. Absolute empirical-coverage error no greater than `0.03` at P50/P90/P95/P99.
3. Quantile-crossing rate no greater than `0.05`.
4. Finite outputs and serving features available at prediction time.
5. An immutable metadata, evaluation, and evidence bundle.

A failed candidate remains research evidence; thresholds are not changed after the evaluation window is observed.

## Architecture

```text
ERCOT Public API ─┐
                  ├─ FastAPI evidence + data layer ── Next.js product UI
Weather sources ──┘               │
                                  ├─ artifact validation gate
                                  ├─ risk and scenario services
                                  └─ SQLite/PostgreSQL persistence
```

- **Frontend:** Next.js 16, React 18, TypeScript, Tailwind CSS, Recharts.
- **Backend:** FastAPI, Pydantic 2, SQLAlchemy 2, NumPy/SciPy/scikit-learn.
- **Production:** Vercel frontend and Railway containerized backend.
- **Security:** explicit production CORS, request IDs, rate limits, no-store API responses, browser security headers, non-root container, and server-only credentials.

## Local development

Requirements:

- Node.js 22+
- Python 3.12+

```bash
git clone https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-.git
cd Grid-Extreme-Risk-Toolkit-GERT-

npm ci
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt -r requirements-training.txt

cp .env.example .env
```

Run the backend and frontend in separate terminals:

```bash
APP_ENV=development MODEL_BACKEND=stub ./.venv/bin/uvicorn api.app:app --reload --port 8000
NEXT_PUBLIC_API_URL=http://localhost:8000 NEXT_PUBLIC_DATA_MODE=live npm run dev
```

Open `http://localhost:3000`; API documentation is at `http://localhost:8000/docs`.

The stub is available for development, but production deliberately refuses stub predictions. To run a real artifact, set `MODEL_BACKEND=real` and `MODEL_ARTIFACT_DIR` to a validated artifact directory.

## Configuration

Backend secrets belong only in Railway or a local ignored environment file. Never expose them with a `NEXT_PUBLIC_` prefix.

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `development`, `test`, or `production` |
| `ALLOWED_ORIGINS` | Comma-separated exact frontend origins |
| `DATABASE_URL` | SQLite or PostgreSQL connection string |
| `MODEL_BACKEND` | `stub` or `real` |
| `MODEL_ARTIFACT_DIR` | Required for `MODEL_BACKEND=real` |
| `ERCOT_API_USERNAME` | ERCOT Public API credential, backend only |
| `ERCOT_API_PASSWORD` | ERCOT Public API credential, backend only |
| `ERCOT_API_SUBSCRIPTION_KEY` | ERCOT subscription key, backend only |
| `NEXT_PUBLIC_API_URL` | Public backend base URL compiled into the frontend |
| `NEXT_PUBLIC_DATA_MODE` | `live` for public use; `demo` only for explicit presentation builds |

See [`.env.example`](.env.example) for the full template.

## Verification

```bash
# Backend and model contracts
./.venv/bin/python -m pytest -q

# Frontend
npm run lint
npm run test:frontend
npm run build

# Dependency security
npm audit --audit-level=high
./.venv/bin/pip-audit -r requirements.txt --progress-spinner off

# Container
docker build -t gert-backend .
```

CI repeats the tests, typecheck, dependency audits, production build, container readiness, production stub gate, CORS checks, and security-header checks.

## API truth-state endpoints

- `GET /health` — process liveness and active backend label.
- `GET /ready` — database readiness.
- `GET /status` — public capability state without configuration or secrets.
- `GET /model/evidence` — versioned sanitized candidate evaluation.
- `GET /load/current?region=ERCOT_SYSTEM` — current operating context.
- `POST /predict` — probabilistic inference; gated in production without a validated artifact.

## License

MIT
