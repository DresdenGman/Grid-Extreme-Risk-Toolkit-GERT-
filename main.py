"""
GERT backend entrypoint.

The production code has been refactored into layered modules:
- api/        HTTP layer (routers + schemas + app wiring)
- services/   business logic (prediction/scoring/scenarios)
- models/     model adapters + quantile post-processing
- features/   feature engineering
- risk/       decision rules (scoring + financials)
"""

from api.app import app

if __name__ == "__main__":
    import uvicorn
    # Local development entry point
    uvicorn.run(app, host="0.0.0.0", port=8000)
